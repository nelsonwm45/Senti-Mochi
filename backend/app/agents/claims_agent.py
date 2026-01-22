
from typing import Dict, Any, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import DocumentChunk
from app.agents.base import get_llm
from app.agents.state import AgentState
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
    """
    print(f"Claims Agent: Analyzing documents for company {state['company_name']}")
    
    try:
        model = get_embedding_model()
        query = "Company strategy, key risks, future outlook, and management guidance."
        query_vector = model.encode(query).tolist()
        
        with Session(engine) as session:
            # Vector search using pgvector
            # We need to filter by company's documents.
            # DocumentChunk -> Document -> Company
            # Join is needed.
            from app.models import Document
            
            # Using raw SQL for vector search + join might be easier, or SQLModel select
            # SQLModel doesn't strictly support pgvector operators in pythonic way easily without func
            # But we can use order_by(DocumentChunk.embedding.l2_distance(query_vector))
            
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
        
        return {"claims_analysis": response.content}
        
    except Exception as e:
        print(f"Error in Claims Agent: {e}")
        return {"claims_analysis": f"Error analyzing documents: {str(e)}", "errors": [str(e)]}
