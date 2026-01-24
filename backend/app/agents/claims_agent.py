
from typing import Dict, Any, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import DocumentChunk, Document
from app.agents.base import get_llm
from app.agents.state import AgentState, CitedFact, SourceReference
from app.agents.cache import generate_cache_key, hash_content, get_cached_result, set_cached_result
from langchain_core.messages import SystemMessage, HumanMessage
import json
import itertools
import warnings

warnings.filterwarnings("ignore")

from app.services.embedding_service import embedding_service


def claims_agent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes documents via RAG with full citation tracking.
    FEATURE 1: Every extracted claim carries document source, page number, and confidence.
    """
    print(f"Claims Agent: Analyzing documents for company {state['company_name']}")
    
    # FEATURE 5: Polymorphic Analysis Search Focus
    user_role = state.get("user_role", "investor")
    print(f"Claims Focus ({user_role})")

    sources: List[dict] = state.get('sources', []) or []
    claims_facts: List[dict] = []
    doc_id_to_citation: Dict[str, str] = {}  # Map document IDs to citation IDs

    try:
        # 1. Environment & Climate Query
        env_query = "Net Zero 2050 NZBA, Just Transition, SBTi, Carbon Neutrality, PCAF Financed Emissions Scope 3, TNFD, NDPE, HCV."

        # 2. Social & Impact Query
        social_query = "Financial Inclusion MSMEs, Human Rights, Modern Slavery, Supply Chain ESG, DEIB Diversity Equity Inclusion."

        # 3. Governance & Risk Query
        gov_query = "Board Sustainability Committee, Enterprise Risk Management ERM, Anti-Bribery Corruption ABC."

        # 4. Disclosure & Standards Query
        disclosure_query = "ISSB IFRS S1 S2, SASB, TCFD, Materiality Assessment."

        # Encode all queries
        env_vector = embedding_service.generate_embeddings([env_query])[0]
        social_vector = embedding_service.generate_embeddings([social_query])[0]
        gov_vector = embedding_service.generate_embeddings([gov_query])[0]
        disclosure_vector = embedding_service.generate_embeddings([disclosure_query])[0]

        # FEATURE 5: Role-based Retrieval Weights
        # Adjusting the number of chunks fetched per category based on user role
        limits = {
            "env": 50, "social": 50, "gov": 50, "disc": 50
        }
        
        if user_role == "investor":
            limits = {"env": 40, "social": 30, "gov": 40, "disc": 60} # Focus on Disclosure/Financials
        elif user_role == "credit_risk":
            limits = {"env": 30, "social": 20, "gov": 80, "disc": 40} # Focus on Governance/Risk
        elif user_role == "relationship_manager":
            limits = {"env": 40, "social": 80, "gov": 30, "disc": 30} # Focus on Social/Impact
        elif user_role == "market_analyst":
            limits = {"env": 40, "social": 30, "gov": 40, "disc": 80} # Heavy focus on Disclosure/Relativity

        print(f"Claims Limits ({user_role}): {limits}")

        with Session(engine) as session:
            # Fetch Environment Chunks
            env_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == state["company_id"])
                .order_by(DocumentChunk.embedding.l2_distance(env_vector))
                .limit(limits["env"])
            )
            env_chunks = session.exec(env_statement).all()

            # Fetch Social Chunks
            social_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == state["company_id"])
                .order_by(DocumentChunk.embedding.l2_distance(social_vector))
                .limit(limits["social"])
            )
            social_chunks = session.exec(social_statement).all()

            # Fetch Governance Chunks
            gov_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == state["company_id"])
                .order_by(DocumentChunk.embedding.l2_distance(gov_vector))
                .limit(limits["gov"])
            )
            gov_chunks = session.exec(gov_statement).all()

            # Fetch Disclosure Chunks
            disc_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == state["company_id"])
                .order_by(DocumentChunk.embedding.l2_distance(disclosure_vector))
                .limit(limits["disc"])
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

            # Limit to top 15 unique chunks (reduced for token limits)
            all_chunks = unique_chunks[:15]

            if not all_chunks:
                print("Claims Agent: No chunks found!")
                return {
                    "claims_analysis": "No relevant document chunks found.",
                    "claims_facts": [],
                    "sources": sources
                }

            print(f"Claims Agent: Retrieved {len(all_chunks)} unique chunks.")

            # Build citation-aware context
            chunk_texts = []
            doc_citation_counter = len([s for s in sources if s.get('type') == 'document']) + 1

            for chunk in all_chunks:
                doc_id_str = str(chunk.document_id)

                # Get or create citation for this document
                if doc_id_str not in doc_id_to_citation:
                    # Fetch document metadata
                    doc = session.get(Document, chunk.document_id)
                    if doc:
                        citation_id = f"D{doc_citation_counter}"
                        doc_citation_counter += 1
                        doc_id_to_citation[doc_id_str] = citation_id

                        # Register source
                        source_ref = SourceReference(
                            id=citation_id,
                            type="document",
                            title=doc.filename,
                            url=None,  # Internal documents don't have URLs
                            date=str(doc.upload_date.date()) if doc.upload_date else None,
                            page=chunk.page_number
                        )
                        sources.append(source_ref.model_dump())

                citation_id = doc_id_to_citation.get(doc_id_str, "D?")
                page_info = f"Page {chunk.page_number}" if chunk.page_number else "Unknown page"

                # Truncate chunk content for token management
                chunk_content = chunk.content[:800] if len(chunk.content) > 800 else chunk.content

                chunk_texts.append(
                    f"[{citation_id}] Source: {page_info}\nContent: {chunk_content}"
                )

                # Create cited fact
                doc = session.get(Document, chunk.document_id)
                fact = CitedFact(
                    content=chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content,
                    source_url=None,
                    source_title=doc.filename if doc else "Unknown Document",
                    source_date=str(doc.upload_date.date()) if doc and doc.upload_date else None,
                    source_type="document",
                    page_number=chunk.page_number,
                    confidence=0.85,
                    citation_id=citation_id
                )
                claims_facts.append(fact.model_dump())

        context = "\n---\n".join(chunk_texts)

        # Token limit management (reduced for Groq 6000 TPM)
        if len(context) > 10000:
            context = context[:10000] + "..."

        # Generate cache key
        chunk_ids = [str(c.id) for c in all_chunks]
        content_for_hash = context + "|" + ",".join(chunk_ids)
        content_hash = hash_content(content_for_hash)
        cache_key = generate_cache_key("claims_v2", state["company_id"], content_hash)

        # Check cache
        cached_result = get_cached_result(cache_key)
        if cached_result:
            try:
                cached_data = json.loads(cached_result)
                return {
                    "claims_analysis": cached_data.get("analysis", cached_result),
                    "claims_facts": cached_data.get("facts", claims_facts),
                    "sources": cached_data.get("sources", sources)
                }
            except:
                return {"claims_analysis": cached_result, "claims_facts": claims_facts, "sources": sources}

        prompt = f"""You are a Claims Analyst. Verify and analyze claims from company documents.

CRITICAL INSTRUCTION - CITATION RULES:
- Each document excerpt has a citation ID like [D1], [D2], etc.
- You MUST cite sources when extracting claims using these IDs.
- Example: "The company targets Net Zero by 2050 [D1]" or "Scope 1 emissions: 15,000 tCO2e [D2]"

Document Excerpts:
{context}

Focus on extracting SPECIFIC DATA POINTS with citations:
1. ESG Targets & Commitments (with citations)
2. Emissions Data (Scope 1, 2, 3) (with citations)
3. Frameworks mentioned (TCFD, GRI, SASB) (with citations)
4. Policies and governance (with citations)
5. Risk disclosures (with citations)

CRITICAL: Do NOT use generic statements. Extract EXACT figures and cite them.
Every claim MUST have a citation marker like [D1], [D2], etc."""

        llm = get_llm("llama-3.1-8b-instant")
        response = llm.invoke([
            SystemMessage(content="You are an expert due diligence analyst. Always cite document sources using [D1], [D2] format."),
            HumanMessage(content=prompt)
        ])

        analysis = response.content

        # Cache result with metadata
        cache_data = json.dumps({
            "analysis": analysis,
            "facts": claims_facts,
            "sources": sources
        })
        set_cached_result(cache_key, cache_data)

        return {
            "claims_analysis": analysis,
            "claims_facts": claims_facts,
            "sources": sources
        }

    except Exception as e:
        print(f"Error in Claims Agent: {e}")
        return {
            "claims_analysis": f"Error analyzing documents: {str(e)}",
            "claims_facts": [],
            "sources": sources,
            "errors": [str(e)]
        }


def claims_debate(state: AgentState) -> Dict[str, Any]:
    """
    FEATURE 3: Structured Debate - Claims Agent provides Bull/Bear arguments.
    """
    print(f"Claims Agent: Structured debate for {state['company_name']}")

    news_analysis = state.get("news_analysis", "No news analysis provided.")
    financial_analysis = state.get("financial_analysis", "No financial analysis provided.")
    my_analysis = state.get("claims_analysis", "No claims analysis provided.")

    # Truncate inputs for token limits
    if len(news_analysis) > 3000:
        news_analysis = news_analysis[:3000] + "..."
    if len(financial_analysis) > 3000:
        financial_analysis = financial_analysis[:3000] + "..."
    if len(my_analysis) > 3000:
        my_analysis = my_analysis[:3000] + "..."

    prompt = f"""You are a Claims/Documents Analyst participating in an investment debate.
    ROLE FOCUS: You are arguing from the perspective of a {state.get('user_role', 'investor')}.

Based on the company documents and other analyses, construct a STRUCTURED DEBATE output.

1. CLAIMS/DOCUMENTS ANALYSIS (Your Context):
{my_analysis}

2. NEWS ANALYSIS:
{news_analysis}

3. FINANCIAL ANALYSIS:
{financial_analysis}

OUTPUT FORMAT (JSON):
{{
    "bull_argument": {{
        "claim": "Main bullish thesis from documents perspective (ESG strength, governance, etc.)",
        "supporting_facts": ["[D1]", "[D2]"],
        "strength": "strong|moderate|weak"
    }},
    "bear_argument": {{
        "claim": "Main bearish thesis (gaps in disclosure, greenwashing risks, etc.)",
        "supporting_facts": ["[D1]"],
        "strength": "strong|moderate|weak"
    }},
    "evidence_clash": ["List where documents contradict news or financials"],
    "winning_side": "bull|bear|undecided",
    "reasoning": "Why this side is stronger based on document evidence"
}}

Respond ONLY with valid JSON."""

    llm = get_llm("llama-3.1-8b-instant")
    response = llm.invoke([
        SystemMessage(content="You output structured JSON for investment debates based on document analysis."),
        HumanMessage(content=prompt)
    ])

    # Parse response
    try:
        debate_output = json.loads(response.content)
    except:
        debate_output = {
            "bull_argument": {"claim": "Strong ESG disclosures", "supporting_facts": [], "strength": "moderate"},
            "bear_argument": {"claim": "Gaps in data coverage", "supporting_facts": [], "strength": "moderate"},
            "evidence_clash": [],
            "winning_side": "undecided",
            "reasoning": response.content[:500]
        }

    return {"claims_debate": debate_output, "claims_critique": response.content}


def claims_critique(state: AgentState) -> Dict[str, Any]:
    """
    Legacy critique function - now calls claims_debate for structured output.
    """
    return claims_debate(state)
