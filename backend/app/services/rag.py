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
        company_ids: Optional[List[UUID]] = None,
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
            print(f"Vector search query user: {user_id}, companies: {company_ids}")

            # Base query with security check - MUST filter by user_id
            # Also filter by company_ids if provided (include global docs with null company_id)
            company_filter = ""
            if company_ids and len(company_ids) > 0:
                ids_str = ",".join([f"'{str(cid)}'" for cid in company_ids])
                company_filter = f"AND (d.company_id IN ({ids_str}) OR d.company_id IS NULL)"

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
                  {company_filter}
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

    def get_structured_chunks(self, query: str) -> List[Dict]:
        """
        Identify companies in query and fetch structured data as Chunks.
        """
        from app.services.company_service import company_service
        
        with Session(engine) as session:
            companies = company_service.find_companies_by_text(query, session)
            if not companies:
                return []
            return self.get_structured_chunks_for_companies(companies, session)

    def get_structured_chunks_for_companies(self, companies: List, session: Session) -> List[Dict]:
        """
        Fetch structured data chunks for a specific list of companies.
        """
        # Lazy imports
        from app.services.news_service import news_service
        from app.services.finance import finance_service
        from uuid import uuid4
        
        chunks = []
        
        for company in companies:
            # 1. Fetch Financials
            try:
                fin_ctx = finance_service.get_financials_context(company.ticker)
                if fin_ctx:
                    chunks.append({
                        "id": uuid4(),
                        "document_id": None,
                        "content": fin_ctx,
                        "page_number": 1,
                        "chunk_index": 0,
                        "metadata": {"type": "financials", "company": company.ticker},
                        "filename": f"Financial Data ({company.name})",
                        "similarity": 1.0, # High relevance
                        "start_line": None,
                        "end_line": None
                    })
            except Exception as e:
                print(f"Error fetching financials chunks for {company.ticker}: {e}")
            
            # 2. Fetch News
            try:
                news_ctx = news_service.get_company_news_context(company.id, session)
                if news_ctx:
                    chunks.append({
                        "id": uuid4(),
                        "document_id": None,
                        "content": news_ctx,
                        "page_number": 1,
                        "chunk_index": 0,
                        "metadata": {"type": "news", "company": company.ticker},
                        "filename": f"News Feed ({company.name})",
                        "similarity": 1.0,
                        "start_line": None,
                        "end_line": None
                    })
            except Exception as e:
                print(f"Error fetching news chunks for {company.ticker}: {e}")
                
        return chunks
    
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
        chat_history: List[Dict] = None, # List of {"role": "...", "content": "..."}
        model: str = "llama-3.3-70b-versatile",  # Groq's fast model
        temperature: float = 0.7
    ) -> Dict:
        """
        Generate response using Groq with context
        
        Returns:
            Dict with 'response' and extracted 'citations'
        """
        # ... (Prompt construction remains same) ...
        prompt = f"""You are a knowledgeable finance expert assistant. 
Your role is to provide accurate, helpful financial advice based on the provided context, which may include user documents, financial data, and news.

CRITICAL RULES:
1. Use the provided context to answer the user's questions. Context acts as your knowledge base.
2. If the user greets you or asks general questions, answer politely.
3. If the user asks a specific question and the context contains relevant data (financials, news, or documents), answer CONFIDENTLY based on that data.
4. DO NOT apologize for missing "documents" if you have financial data or news that answers the question.
5. Only say you couldn't find information if the ENTIRE context is empty or irrelevant to the question.
6. Always cite sources using [Source N] format.
7. Be precise with financial data.
8. Handle PII carefully.

Context:
{context}

---

User Question: {query}

Answer (cite sources as [Source 1], [Source 2], etc.):"""
        
        # Build messages list
        messages = [{"role": "system", "content": "You are a helpful finance expert assistant."}]
        
        # Inject History
        if chat_history:
            # We only strictly need the 'role' and 'content' fields
            for msg in chat_history:
                if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                    messages.append({"role": msg['role'], "content": msg['content']})
        
        # Add current turn
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
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
        chat_history: List[Dict] = None,
        model: str = "llama-3.3-70b-versatile"
    ):
        """
        Generate streaming response (for real-time UI updates)
        
        Yields:
            Response chunks as they're generated
        """
        # ... (Prompt construction remains same) ...
        prompt = f"""You are a knowledgeable finance expert assistant. 
Your role is to provide accurate, helpful financial advice based on the provided context, which may include user documents, financial data, and news.

CRITICAL RULES:
1. Use the provided context to answer the user's questions. Context acts as your knowledge base.
2. If the user greets you or asks general questions, answer politely.
3. If the user asks a specific question and the context contains relevant data (financials, news, or documents), answer CONFIDENTLY based on that data.
4. DO NOT apologize for missing "documents" if you have financial data or news that answers the question.
5. Only say you couldn't find information if the ENTIRE context is empty or irrelevant to the question.
6. Always cite sources using [Source N] format.
7. Be precise with financial data.
8. Handle PII carefully.

Context:
{context}

---

User Question: {query}

Answer (cite sources as [Source 1], [Source 2], etc.):"""
        
        # Build messages list
        messages = [{"role": "system", "content": "You are a helpful finance expert assistant."}]
        
        if chat_history:
            for msg in chat_history:
                if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                    messages.append({"role": msg['role'], "content": msg['content']})
        
        messages.append({"role": "user", "content": prompt})

        stream = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            max_tokens=1024
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
