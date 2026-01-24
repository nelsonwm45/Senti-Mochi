
from typing import Dict, Any, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import DocumentChunk
from app.agents.base import get_llm
from app.agents.state import AgentState
from app.agents.cache import generate_cache_key, hash_content, get_cached_result, set_cached_result
from app.agents.persona_config import get_persona_config
from langchain_core.messages import SystemMessage, HumanMessage
from sentence_transformers import SentenceTransformer
import warnings

# Suppress connection warnings if any
warnings.filterwarnings("ignore")

# Global model instance to avoid reloading (lazy load?)
from app.services.embedding_service import embedding_service

def claims_agent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes documents via RAG.
    Uses caching to ensure consistent results for unchanged data.
    Adapts queries based on analysis_persona.
    """
    persona = state.get('analysis_persona', 'INVESTOR')
    config = get_persona_config(persona)
    print(f"Claims Agent: Analyzing documents for company {state['company_name']} [Persona: {persona}]")

    try:
        # Use persona-specific queries for each ESG category
        env_query = config['claims_queries']['environmental']
        social_query = config['claims_queries']['social']
        gov_query = config['claims_queries']['governance']
        disclosure_query = config['claims_queries']['disclosure']

        # For Credit Risk persona, governance is highest priority - fetch more governance chunks
        is_credit_risk = persona == 'CREDIT_RISK'

        # Encode all queries
        env_vector = embedding_service.generate_embeddings([env_query])[0]
        social_vector = embedding_service.generate_embeddings([social_query])[0]
        gov_vector = embedding_service.generate_embeddings([gov_query])[0]
        disclosure_vector = embedding_service.generate_embeddings([disclosure_query])[0]

        with Session(engine) as session:
            from app.models import Document

            # Fetch Environment Chunks
            env_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == state["company_id"])
                .order_by(DocumentChunk.embedding.l2_distance(env_vector))
                .limit(100)
            )
            env_chunks = session.exec(env_statement).all()
            
            # Fetch Social Chunks
            social_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == state["company_id"])
                .order_by(DocumentChunk.embedding.l2_distance(social_vector))
                .limit(100)
            )
            social_chunks = session.exec(social_statement).all()
            
            # Fetch Governance Chunks
            # For Credit Risk persona, governance is highest priority - fetch more
            gov_limit = 150 if is_credit_risk else 100
            gov_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == state["company_id"])
                .order_by(DocumentChunk.embedding.l2_distance(gov_vector))
                .limit(gov_limit)
            )
            gov_chunks = session.exec(gov_statement).all()

            # Fetch Disclosure Chunks
            disc_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == state["company_id"])
                .order_by(DocumentChunk.embedding.l2_distance(disclosure_vector))
                .limit(100)
            )
            disc_chunks = session.exec(disc_statement).all()

            # Combine and deduplicate
            unique_chunks = []
            seen_content = set()
            
            # Interleave results
            import itertools
            for chunk in itertools.chain.from_iterable(itertools.zip_longest(env_chunks, social_chunks, gov_chunks, disc_chunks)):
                if chunk and chunk.content not in seen_content:
                    unique_chunks.append(chunk)
                    seen_content.add(chunk.content)
            
            # Limit to top 20 unique chunks (increased from 15 to cover more ground)
            all_chunks = unique_chunks[:20]

            if not all_chunks:
                print("Claims Agent: No chunks found!")
                return {"claims_analysis": "No relevant document chunks found."}
            
            print(f"Claims Agent: Retrieved {len(all_chunks)} unique chunks.")

            chunk_texts = [f"Source: Doc {c.document_id} (Page {c.page_number})\nContent: {c.content}" for c in all_chunks]
            
        context = "\n---\n".join(chunk_texts)

        # Check token limit roughly (characters / 4)
        # Reduced to 15000 to fit within Groq's 6000 TPM limit (approx 3750 tokens)
        if len(context) > 15000:
            context = context[:15000] + "..."

        # Generate cache key based on content hash
        # Include chunk IDs in hash to detect if documents changed
        chunk_ids = [str(c.id) for c in all_chunks]
        content_for_hash = context + "|" + ",".join(chunk_ids)
        content_hash = hash_content(content_for_hash)
        cache_key = generate_cache_key("claims", state["company_id"], content_hash)

        # Check cache first
        cached_result = get_cached_result(cache_key)
        if cached_result:
            return {"claims_analysis": cached_result}

        # Build persona-specific prompt
        focus_areas = ", ".join(config['claims_focus'])
        persona_label = persona.replace('_', ' ').title()

        # Build priority note for Credit Risk
        priority_note = ""
        if is_credit_risk:
            priority_note = "\n\n**HIGHEST PRIORITY: Governance** - Flag any fraud risks, weak internal controls, board independence issues, or related party transactions."

        prompt = f"""You are a Claims/Documents Analyst serving a {persona_label}.

        YOUR SPECIFIC FOCUS AREAS: {focus_areas}{priority_note}

        Your job is to verify and analyze the claims made by the company in their documents.
        Prioritize extracting information relevant to: {focus_areas}

        Document Excerpts:
        {context}

        Synthesize these findings into a Markdown report.

        CRITICAL INSTRUCTION:
        Do NOT summarize generic statements (e.g. "Company is committed to ESG").
        EXTRACT AND LIST SPECIFIC DATA POINTS relevant to a {persona_label}:
        - Exact figures, dates, targets
        - Specific frameworks and certifications
        - Policy names and commitments
        - Risk disclosures and mitigation measures

        If precise numbers are found, bold them."""

        llm = get_llm("llama-3.1-8b-instant")
        response = llm.invoke([SystemMessage(content="You are an expert due diligence analyst."), HumanMessage(content=prompt)])

        # Cache the result
        set_cached_result(cache_key, response.content)

        return {"claims_analysis": response.content}

    except Exception as e:
        print(f"Error in Claims Agent: {e}")
        return {"claims_analysis": f"Error analyzing documents: {str(e)}", "errors": [str(e)]}

def claims_critique(state: AgentState) -> Dict[str, Any]:
    """
    Critiques other agents' findings based on Internal Claims/Documents.
    Uses persona-specific debate stances.
    """
    persona = state.get('analysis_persona', 'INVESTOR')
    config = get_persona_config(persona)
    persona_label = persona.replace('_', ' ').title()
    print(f"Claims Agent: Critiquing findings for {state['company_name']} [Persona: {persona}]")

    news_analysis = state.get("news_analysis", "No news analysis provided.")
    financial_analysis = state.get("financial_analysis", "No financial analysis provided.")
    my_analysis = state.get("claims_analysis", "No claims analysis provided.")

    prompt = f"""You are a Claims/Documents Analyst in a structured debate for a {persona_label}.

    DEBATE CONTEXT:
    - GOVERNMENT (Pro) Stance: {config['government_stance']}
    - OPPOSITION (Skeptic) Stance: {config['opposition_stance']}

    You are providing an OBJECTIVE assessment. Use official documents to verify or challenge other findings.

    Your Task:
    Critique the findings from the News Analyst and Financial Analyst based on official company documents.
    - Does News misinterpret the company's stated strategy?
    - Do Financials align with company guidance and outlook?
    - Are there undisclosed risks in documents that others missed?

    1. CLAIMS ANALYSIS (Your Context):
    {my_analysis}

    2. NEWS ANALYSIS (To Critique):
    {news_analysis}

    3. FINANCIAL ANALYSIS (To Critique):
    {financial_analysis}

    Provide a concise critique (max 200 words) focusing on document evidence.
    """

    llm = get_llm("llama-3.1-8b-instant")
    response = llm.invoke([SystemMessage(content=f"You are a diligent document analyst serving a {persona_label}."), HumanMessage(content=prompt)])

    return {"claims_critique": response.content}
