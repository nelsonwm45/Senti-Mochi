"""
Claims Agent - The Auditor

Analyzes documents via RAG with citation tracking.
Generates [D1], [D2], ... citations mapping to {file_name, page_number, file_link}.
Focus: Governance, Environmental, Social, Disclosure Quality.
"""

from typing import Dict, Any, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import DocumentChunk, Document
from app.agents.base import get_llm
from app.agents.state import AgentState
from app.agents.cache import generate_cache_key, hash_content, get_cached_result, set_cached_result
from app.agents.persona_config import get_persona_config
from app.agents.prompts import CLAIMS_AGENT_SYSTEM, get_claims_agent_prompt, get_critique_prompt
from app.agents.citation_models import SourceMetadata
from langchain_core.messages import SystemMessage, HumanMessage
from sentence_transformers import SentenceTransformer
import warnings
import itertools
import os

# Suppress connection warnings
warnings.filterwarnings("ignore")

# Global embedding service
from app.services.embedding_service import embedding_service


def claims_agent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes documents via RAG with citation tracking.

    Citation Protocol:
    - Each document chunk gets a [D#] citation
    - Maps to {file_name, page_number, file_link}

    Returns:
        Dict with claims_analysis and citation_registry updates
    """
    persona = state.get('analysis_persona', 'INVESTOR')
    config = get_persona_config(persona)
    company_id = state["company_id"]
    company_name = state["company_name"]

    print(f"Claims Agent: Analyzing documents for {company_name} [Persona: {persona}]")

    # Initialize citation registry if not present
    citation_registry = dict(state.get('citation_registry', {}))

    try:
        # Use persona-specific queries for each ESG category
        env_query = config['claims_queries']['environmental']
        social_query = config['claims_queries']['social']
        gov_query = config['claims_queries']['governance']
        disclosure_query = config['claims_queries']['disclosure']

        # For Credit Risk persona, governance is highest priority
        is_credit_risk = persona == 'CREDIT_RISK'

        # Encode all queries
        env_vector = embedding_service.generate_embeddings([env_query])[0]
        social_vector = embedding_service.generate_embeddings([social_query])[0]
        gov_vector = embedding_service.generate_embeddings([gov_query])[0]
        disclosure_vector = embedding_service.generate_embeddings([disclosure_query])[0]

        # WAIT FOR DOCUMENTS: Check if any documents are still processing
        with Session(engine) as session:
            import time
            from app.models import DocumentStatus

            max_retries = 15  # 30 seconds max
            for _ in range(max_retries):
                pending_docs = session.exec(
                    select(Document)
                    .where(Document.company_id == company_id)
                    .where(col(Document.status).in_([DocumentStatus.PENDING, DocumentStatus.PROCESSING]))
                    .where(Document.is_deleted == False)
                ).all()

                if not pending_docs:
                    break
                
                print(f"Claims Agent: Waiting for {len(pending_docs)} documents to process...")
                time.sleep(2)

        with Session(engine) as session:
            # Fetch Environment Chunks
            env_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == company_id)
                .where(Document.is_deleted == False)
                .order_by(DocumentChunk.embedding.l2_distance(env_vector))
                .limit(100)
            )
            env_chunks = session.exec(env_statement).all()

            # Fetch Social Chunks
            social_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == company_id)
                .where(Document.is_deleted == False)
                .order_by(DocumentChunk.embedding.l2_distance(social_vector))
                .limit(100)
            )
            social_chunks = session.exec(social_statement).all()

            # Fetch Governance Chunks (more for Credit Risk)
            gov_limit = 150 if is_credit_risk else 100
            gov_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == company_id)
                .where(Document.is_deleted == False)
                .order_by(DocumentChunk.embedding.l2_distance(gov_vector))
                .limit(gov_limit)
            )
            gov_chunks = session.exec(gov_statement).all()

            # Fetch Disclosure Chunks
            disc_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == company_id)
                .where(Document.is_deleted == False)
                .order_by(DocumentChunk.embedding.l2_distance(disclosure_vector))
                .limit(100)
            )
            disc_chunks = session.exec(disc_statement).all()

            # Combine and deduplicate
            unique_chunks = []
            seen_content = set()

            # Interleave results
            for chunk in itertools.chain.from_iterable(
                itertools.zip_longest(env_chunks, social_chunks, gov_chunks, disc_chunks)
            ):
                if chunk and chunk.content not in seen_content:
                    unique_chunks.append(chunk)
                    seen_content.add(chunk.content)

            # Limit to top 30 unique chunks (increased from 20)
            all_chunks = unique_chunks[:30]

            if not all_chunks:
                print("Claims Agent: No chunks found!")
                return {
                    "claims_analysis": "No relevant document chunks found.",
                    "citation_registry": citation_registry
                }

            print(f"Claims Agent: Retrieved {len(all_chunks)} unique chunks.")

            # Build citation metadata and content
            chunk_texts = []
            source_list_parts = []

            # Get document info for each chunk
            doc_cache = {}

            # Group chunks by document to consolidate citations
            doc_to_citation = {}
            citation_counter = 1
            
            # Map chunk IDs for cache key stability
            chunk_ids = [str(c.id) for c in all_chunks]
            
            for chunk in all_chunks:
                # Assign citation ID based on Document ID
                if chunk.document_id not in doc_to_citation:
                    doc_to_citation[chunk.document_id] = f"D{citation_counter}"
                    citation_counter += 1
                
                citation_id = doc_to_citation[chunk.document_id]

                # Get document info (cached)
                if chunk.document_id not in doc_cache:
                    doc = session.get(Document, chunk.document_id)
                    doc_cache[chunk.document_id] = doc

                doc = doc_cache.get(chunk.document_id)
                doc_name = doc.filename if doc else f"Document {chunk.document_id}"
                
                # Update registry only if not present (or update if needed)
                if citation_id not in citation_registry:
                    print(f"Claims Agent: Registering NEW source {citation_id} -> {doc_name}")
                    citation_registry[citation_id] = {
                        "id": citation_id,
                        "title": doc_name,
                        "url_or_path": f"/api/v1/documents/{doc.id}/download" if doc else "",
                        "type": "Document",
                        "page_number": None, # Consolidated, so page is variable
                        "row_line": "Multiple Chunks"
                    }
                    
                    # Add to source list for prompt (once per doc)
                    source_list_parts.append(f"[{citation_id}] - \"{doc_name}\"")

                # Add content to context with specific page reference
                page_suffix = f", Page {chunk.page_number}" if chunk.page_number else ""
                chunk_texts.append(
                    f"CITATION_ID: [{citation_id}{page_suffix}]\n"
                    f"Source: {doc_name}\n"
                    f"Content: {chunk.content}"
                )

        print(f"Claims Agent: Final registry keys before return: {list(citation_registry.keys())}")
        
        context = "\n---\n".join(chunk_texts)
        source_list = "\n".join(source_list_parts)

        # Truncation Logic with Fallback Strategy
        full_context = context

        # Generate cache key based on content hash (Move this UP before try/except)
        # Use v5 to invalidate previous caches AGAIN to be sure
        content_for_hash = full_context + "|" + ",".join(chunk_ids)
        content_hash = hash_content(content_for_hash)
        cache_key = generate_cache_key("claims_v12", company_id, content_hash)
        
        # Check cache first
        cached_result = get_cached_result(cache_key)
        if cached_result:
            print("Claims Agent: Cache HIT. Returning registry.")
            return {
                "claims_analysis": cached_result,
                "citation_registry": citation_registry
            }

        # Attempt Primary: Cerebras (llama-3.3-70b)
        try:
            print(f"[Claims Agent] Attempting to use Cerebras (llama-3.3-70b)...")
            prompt = get_claims_agent_prompt(
                company_name=company_name,
                persona=persona,
                claims_context=full_context,
                source_list=source_list
            )

            llm = get_llm("llama-3.3-70b")
            response = llm.invoke([
                SystemMessage(content=CLAIMS_AGENT_SYSTEM),
                HumanMessage(content=prompt)
            ])
            print(f"[Claims Agent] SUCCESS: Processed by Cerebras (llama-3.3-70b)")
            
            set_cached_result(cache_key, response.content)

            return {
                "claims_analysis": response.content,
                "citation_registry": citation_registry
            }

        except Exception as e:
            print(f"[Claims Agent] Cerebras failed: {e}. Fallback to Groq (llama-3.1-8b-instant)...")
            
            # Apply truncation for Groq (8000 chars)
            if len(full_context) > 8000:
                truncated_context = full_context[:8000] + "..."
            else:
                truncated_context = full_context

            prompt = get_claims_agent_prompt(
                company_name=company_name,
                persona=persona,
                claims_context=truncated_context,
                source_list=source_list
            )

            llm = get_llm("llama-3.1-8b-instant")
            response = llm.invoke([
                SystemMessage(content=CLAIMS_AGENT_SYSTEM),
                HumanMessage(content=prompt)
            ])
            print(f"[Claims Agent] SUCCESS: Processed by Groq (llama-3.1-8b-instant)")
            
            set_cached_result(cache_key, response.content)

            return {
                "claims_analysis": response.content,
                "citation_registry": citation_registry
            }

    except Exception as e:
        print(f"Error in Claims Agent: {e}")
        import traceback
        traceback.print_exc()
        return {
            "claims_analysis": f"Error analyzing documents: {str(e)}",
            "citation_registry": citation_registry,
            "errors": [str(e)]
        }


def claims_critique(state: AgentState) -> Dict[str, Any]:
    """
    Critiques other agents' findings based on Internal Claims/Documents.
    Preserves and references all citation IDs.
    """
    persona = state.get('analysis_persona', 'INVESTOR')
    persona_label = persona.replace('_', ' ').title()
    print(f"Claims Agent: Critiquing findings for {state['company_name']} [Persona: {persona}]")

    news_analysis = state.get("news_analysis", "No news analysis provided.")
    financial_analysis = state.get("financial_analysis", "No financial analysis provided.")
    my_analysis = state.get("claims_analysis", "No claims analysis provided.")

    prompt = get_critique_prompt(
        agent_type="claims",
        persona=persona,
        my_analysis=my_analysis,
        other_analysis_1=news_analysis,
        other_analysis_2=financial_analysis,
        analysis_1_name="News Analysis",
        analysis_2_name="Financial Analysis"
    )

    system_msg = f"You are a diligent document analyst serving a {persona_label}. PRESERVE all citation IDs."

    # Attempt Primary: Cerebras
    try:
        print(f"[Claims Agent] Critique: Attempting Cerebras (llama-3.3-70b)...")
        llm = get_llm("llama-3.3-70b")
        response = llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt)
        ])
        print(f"[Claims Agent] Critique: SUCCESS (Cerebras)")
        return {"claims_critique": response.content}
    except Exception as e:
        print(f"[Claims Agent] Critique: Cerebras failed: {e}. Fallback to Groq...")
        llm = get_llm("llama-3.1-8b-instant")
        response = llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt)
        ])
        print(f"[Claims Agent] Critique: SUCCESS (Groq)")
        return {"claims_critique": response.content}
