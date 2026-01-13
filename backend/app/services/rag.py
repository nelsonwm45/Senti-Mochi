from typing import List, Dict, Optional
from uuid import UUID
import openai
import os
from sqlmodel import Session, select, col
from sqlalchemy import func, text
from app.models import DocumentChunk, Document, ChatMessage
from app.database import engine
from sentence_transformers import SentenceTransformer

class RAGService:
    """Service for Retrieval-Augmented Generation using Groq (OpenAI-compatible)"""
    
    def __init__(self):
        # Configure for Groq (for chat completions)
        self.client = openai.OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        
        # Load embedding model (same as ingestion)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for user query using Sentence Transformers
        
        Uses the same model as document ingestion (all-MiniLM-L6-v2)
        to ensure embedding compatibility
        """
        embedding = self.embedding_model.encode(query, show_progress_bar=False)
        return embedding.tolist()
    
    def vector_search(
        self,
        query_embedding: List[float],
        user_id: UUID,
        document_ids: Optional[List[UUID]] = None,
        limit: int = 5,
        threshold: float = 0.4
    ) -> List[Dict]:
        """
        Perform vector similarity search
        
        CRITICAL: Ensures user can only access their own documents (security check)
        """
        with Session(engine) as session:
            # Build query with vector similarity
            embedding_str = f"[{','.join(map(str, query_embedding))}]"
            
            # Log the query for debugging
            print(f"Vector search query: {embedding_str[:50]}... User: {user_id}")

            # Base query with security check - MUST filter by user_id
            query_sql = f"""
                SELECT 
                    dc.id,
                    dc.document_id,
                    dc.content,
                    dc.page_number,
                    dc.chunk_index,
                    dc.metadata_,
                    d.filename,
                    d.user_id,
                    1 - (dc.embedding <=> '{embedding_str}'::vector) as similarity,
                    dc.start_line,
                    dc.end_line
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.user_id = '{str(user_id)}'
                  AND d.is_deleted = false
                  -- AND 1 - (dc.embedding <=> '{embedding_str}'::vector) >= {0.4}
                ORDER BY similarity DESC
                LIMIT {limit}
            """
            
            results = session.execute(text(query_sql)).fetchall()
            print(f"Found {len(results)} chunks. Scores: {[row[8] for row in results]}")
            
            # Format results
            chunks = []
            for row in results:
                chunks.append({
                    "id": row[0],
                    "document_id": row[1],
                    "content": row[2],
                    "page_number": row[3],
                    "chunk_index": row[4],
                    "metadata": row[5],
                    "filename": row[6],
                    "similarity": float(row[8]),
                    "start_line": row[9],
                    "end_line": row[10]
                })
            
            return chunks

    def get_structured_context(self, query: str) -> str:
        """
        Identify companies in query and fetch structured data (Financials/News).
        """
        # Lazy imports to avoid circular dependency
        from app.services.company_service import company_service
        from app.services.news_service import news_service
        from app.services.finance import finance_service
        
        with Session(engine) as session:
            # 1. Identify Company
            company = company_service.find_company_by_text(query, session)
            if not company:
                return ""
            
            context_str = f"--- Structured Database Data for {company.name} ({company.ticker}) ---\n"
            
            # 2. Fetch Financials
            try:
                fin_ctx = finance_service.get_financials_context(company.ticker)
                if fin_ctx:
                    context_str += fin_ctx
            except Exception as e:
                print(f"Error fetching financials context: {e}")
            
            # 3. Fetch News
            try:
                news_ctx = news_service.get_company_news_context(company.id, session)
                if news_ctx:
                    context_str += news_ctx
            except Exception as e:
                print(f"Error fetching news context: {e}")
                
            return context_str + "\n"
    
    def build_context(self, chunks: List[Dict], max_tokens: int = 8000) -> str:
        """Build context string from retrieved chunks"""
        context_parts = []
        total_tokens = 0
        
        for i, chunk in enumerate(chunks):
            # Estimate tokens (rough: 1 word ≈ 1.3 tokens)
            chunk_tokens = len(chunk["content"].split()) * 1.3
            
            if total_tokens + chunk_tokens > max_tokens:
                break
            
            context_parts.append(
                f"[Source {i+1}: {chunk['filename']}, Page {chunk['page_number']}]\n"
                f"{chunk['content']}\n"
            )
            total_tokens += chunk_tokens
        
        return "\n---\n".join(context_parts)
    
    def generate_response(
        self,
        query: str,
        context: str,
        model: str = "llama-3.3-70b-versatile",  # Groq's fast model
        temperature: float = 0.7
    ) -> Dict:
        """
        Generate response using Groq with context
        
        Returns:
            Dict with 'response' and extracted 'citations'
        """
        prompt = f"""You are a knowledgeable finance expert assistant. 
Your role is to provide accurate, helpful financial advice based on the provided context.

CRITICAL RULES:
1. Use the provided context to answer questions about the user's documents.
2. If the user greets you (e.g., "hi", "hello") or asks general questions, answer politely without needing context.
3. If the user asks a specific question about their documents and the context is empty or irrelevant, say you couldn't find that information.
4. Always cite your sources using the format [Source N] when referencing information.
5. Be precise with numbers and financial data.
6. Handle personally identifiable information (PII) carefully.

Context:
{context}

---

User Question: {query}

Answer (remember to cite sources as [Source 1], [Source 2], etc.):"""
        
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful finance expert assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=1024
        )
        
        answer = response.choices[0].message.content
        
        # Extract citations (simple regex to find [Source N])
        import re
        citations = re.findall(r'\[Source (\d+)\]', answer)
        
        return {
            "response": answer,
            "citations": list(set(citations)),  # Unique citations
            "model": model,
            "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
        }
    
    async def generate_response_stream(
        self,
        query: str,
        context: str,
        model: str = "llama-3.3-70b-versatile"
    ):
        """
        Generate streaming response (for real-time UI updates)
        
        Yields:
            Response chunks as they're generated
        """
        prompt = f"""You are a knowledgeable finance expert assistant. 
Your role is to provide accurate, helpful financial advice based on the provided context.

CRITICAL RULES:
1. Use the provided context to answer questions about the user's documents.
2. If the user greets you or asks general questions, answer politely.
3. If the user asks a specific question about their documents and the context is empty, say you couldn't find that information.
4. Always cite sources using [Source N] format.
5. Be precise with financial data.
6. Handle PII carefully.

Context:
{context}

---

User Question: {query}

Answer (cite sources as [Source 1], [Source 2], etc.):"""
        
        stream = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful finance expert assistant."},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            max_tokens=1024
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
