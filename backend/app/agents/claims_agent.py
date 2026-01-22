
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
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def claims_agent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes documents via RAG.
    Uses caching to ensure consistent results for unchanged data.
    """
    print(f"Claims Agent: Analyzing documents for company {state['company_name']}")

    try:
        model = get_embedding_model()
        query = "Company strategy, key risks, future outlook, and management guidance."
        query_vector = model.encode(query).tolist()

        with Session(engine) as session:
            from app.models import Document

            statement = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.company_id == state["company_id"])
                .order_by(DocumentChunk.embedding.l2_distance(query_vector))
                .limit(10)
            )

            chunks = session.exec(statement).all()

            if not chunks:
                return {"claims_analysis": "No relevant document chunks found."}

            chunk_texts = [f"Source: Doc {c.document_id} (Page {c.page_number})\nContent: {c.content}" for c in chunks]

            context = "\n---\n".join(chunk_texts)

        # Generate cache key based on content hash
        # Include chunk IDs in hash to detect if documents changed
        chunk_ids = [str(c.id) for c in chunks]
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

        Document Excerpts:
        {context}

        Synthesize these findings into a Markdown report."""

        llm = get_llm("llama-3.3-70b-versatile")
        response = llm.invoke([SystemMessage(content="You are an expert due diligence analyst."), HumanMessage(content=prompt)])

        # Cache the result
        set_cached_result(cache_key, response.content)

        return {"claims_analysis": response.content}

    except Exception as e:
        print(f"Error in Claims Agent: {e}")
        return {"claims_analysis": f"Error analyzing documents: {str(e)}", "errors": [str(e)]}
