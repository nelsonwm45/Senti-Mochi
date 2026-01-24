
from typing import Dict, Any, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import DocumentChunk
from app.agents.base import get_llm
from app.agents.state import AgentState
from app.agents.cache import generate_cache_key, hash_content, get_cached_result, set_cached_result
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
    """
    print(f"Claims Agent: Analyzing documents for company {state['company_name']}")

    try:
        # 1. Environment & Climate Query
        env_query = "Net Zero 2050 NZBA, Just Transition, SBTi, Sectoral Decarbonisation Pathways (Palm Oil, Power, O&G), PCAF Financed Emissions Scope 3, Carbon Neutrality, Green Energy Tariff, RECs, Stranded Assets, Climate Scenario Analysis NGFS, Physical Risk Acute Chronic, TNFD Nature-positive, NDPE, HCV."
        
        # 2. Social & Impact Query
        social_query = "Humanising Financial Services, VBI Values-based Intermediation, Financial Inclusion MSMEs B40, Human Rights Due Diligence, Modern Slavery, FPIC, Supply Chain ESG screening, Future-Fit Talent, DEIB Diversity Equity Inclusion Belonging, Psychological safety, Employee Engagement Index."
        
        # 3. Governance & Risk Query
        gov_query = "Double Materiality, Board Sustainability Committee BSC, Shariah Governance, Three Lines of Defence, Enterprise Risk Management ERM, Climate Risk Stress Testing CRST, ICAAP, Watchlist Supplier, Anti-Bribery Corruption ABC, Clawback provisions, Scorecard weightage."

        # 4. Disclosure & Standards Query
        disclosure_query = "ISSB IFRS S1 S2, SASB Commercial Banks, TCFD, NSRF National Sustainability Reporting Framework, Limited Assurance ISAE 3000, Data coverage ratios, Interoperability, Materiality Assessment."

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
            gov_statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == state["company_id"])
                .order_by(DocumentChunk.embedding.l2_distance(gov_vector))
                .limit(100)
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

        prompt = f"""You are a Claims Analyst. Your job is to verify and analyze the claims made by the company in their documents.
        Focus on:
        1. Strategic goals
        2. Reported risks
        3. Future guidance/outlook
        4. ESG (Environmental, Social, Governance) commitments and performance (CRITICAL)

        Document Excerpts:
        {context}

        Synthesize these findings into a Markdown report.
        
        CRITICAL INSTRUCTION:
        Do NOT summarize generic statements (e.g. "Company is committed to ESG").
        EXTRACT AND LIST SPECIFIC DATA POINTS:
        - Exact Emissions figures (Scope 1, 2, 3 in tCO2e)
        - Specific Frameworks (NZBA, TNFD, ISSB, GRI) -> Cite them!
        - Concrete Targets (e.g. "Net Zero by 2050", "RM 50B Sustainable Finance by 2024")
        - Policy names (e.g. "Group Sustainability Policy", "NDPE Policy")
        
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
    """
    print(f"Claims Agent: Critiquing findings for {state['company_name']}")
    
    news_analysis = state.get("news_analysis", "No news analysis provided.")
    financial_analysis = state.get("financial_analysis", "No financial analysis provided.")
    my_analysis = state.get("claims_analysis", "No claims analysis provided.")

    prompt = f"""You are a Claims/Documents Analyst. You have already provided your analysis based on company documents.
    Now, review the findings from the News Analyst and the Financial Analyst.
    
    Your Task:
    Critique their findings based on the official company documents/claims.
    - Does the News misinterpret the company's stated strategy?
    - Do the Financials align with the company's guidance and outlook?
    
    1. CLAIMS ANALYSIS (Your Context):
    {my_analysis}

    2. NEWS ANALYSIS (To Critique):
    {news_analysis}

    3. FINANCIAL ANALYSIS (To Critique):
    {financial_analysis}

    Provide a concise critique (max 200 words) focusing on ALIGNMENT WITH COMPANY STATEMENTS.
    """

    llm = get_llm("llama-3.1-8b-instant")
    response = llm.invoke([SystemMessage(content="You are a diligent compliance and strategy analyst."), HumanMessage(content=prompt)])
    
    return {"claims_critique": response.content}
