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
        threshold: float = 0.5
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
                  AND 1 - (dc.embedding <=> '{embedding_str}'::vector) >= {threshold}
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
            
            # 2. Fetch News (Individual Chunks)
            try:
                # Increase limit to 15 to prevent "Annual Report" spam from hiding real news
                articles = news_service.get_recent_articles(company.id, session, limit=15)
                for idx, article in enumerate(articles):
                    content_str = f"[{article.published_at.strftime('%Y-%m-%d')}] {article.title} (Source: {article.source})"
                    if article.content:
                        content_str += f"\nSummary: {article.content}"
                        
                    chunks.append({
                        "id": uuid4(),
                        "document_id": None,
                        "content": content_str,
                        "page_number": 1,
                        "chunk_index": idx,
                        "metadata": {"type": "news", "company": company.ticker, "article_id": str(article.id)},
                        "filename": f"News: {article.title}",
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
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ... (Prompt construction remains same) ...
        prompt = f"""
Role: You are a Senior Market Intelligence Analyst. Your purpose is to provide end-to-end market analysis, helping banking teams transform unstructured market signals into defensible, consistent investment or strategic decisions.

Current Time: {current_time}

CRITICAL ADHERENCE RULES
1. Strict Domain Focus: You are prohibited from answering general knowledge questions (e.g., "What is the capital of France?" or "How do I bake a cake?").
2. Redirection Protocol: If a user asks a general or non-finance question, you must provide a polite, single-sentence acknowledgment of the query, followed immediately by a redirection to your core functions.
3. Standard Refusal: "I specialize in market intelligence and banking-grade financial analysis. Please provide a ticker, sector, or market signal for me to analyze."
4. Data-Driven Responses: Always prioritize provided context (documents, news, financials). If the data is present, answer with institutional-grade confidence.
5. No Hallucinations: If data is missing for a calculation or analysis, state "Data Not Available." Never guess.
6. PII Protection: Redact any sensitive information (e.g., account numbers) and warn the user immediately.

OUTPUT FORMATTING
1. Calculations: Must show the formula and step-by-step math.
2. Comparisons: Always use Markdown tables for numerical or feature comparisons.
3. Data Extraction: If the user requests data parsing, output strictly in JSON format with no conversational filler.
4. Tone: Maintain an institutional, objective tone. Use terms like "high volatility" or "strategic alignment" instead of "exciting" or "massive."

CITATION PROTOCOL
1. Only cite sources using the [Source N] format if the information is explicitly found in the provided context.
2. If no context is provided, answer using internal knowledge but do not use citations.


Context:
{context if context else "[No relevant documents found]"}

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
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ... (Prompt construction remains same) ...
        prompt = f"""
Role: You are a Senior Market Intelligence Analyst. Your purpose is to provide end-to-end market analysis, helping banking teams transform unstructured market signals into defensible, consistent investment or strategic decisions.

CRITICAL ADHERENCE RULES
1. Strict Domain Focus: You are prohibited from answering general knowledge questions (e.g., "What is the capital of France?" or "How do I bake a cake?").
2. Redirection Protocol: If a user asks a general or non-finance question, you must provide a polite, single-sentence acknowledgment of the query, followed immediately by a redirection to your core functions.
3. Standard Refusal: "I specialize in market intelligence and banking-grade financial analysis. Please provide a ticker, sector, or market signal for me to analyze."
4. Data-Driven Responses: Always prioritize provided context (documents, news, financials). If the data is present, answer with institutional-grade confidence.
5. No Hallucinations: If data is missing for a calculation or analysis, state "Data Not Available." Never guess.
6. PII Protection: Redact any sensitive information (e.g., account numbers) and warn the user immediately.

OUTPUT FORMATTING
1. Calculations: Must show the formula and step-by-step math.
2. Comparisons: Always use Markdown tables for numerical or feature comparisons.
3. Data Extraction: If the user requests data parsing, output strictly in JSON format with no conversational filler.
4. Tone: Maintain an institutional, objective tone. Use terms like "high volatility" or "strategic alignment" instead of "exciting" or "massive."

CITATION PROTOCOL
1. Only cite sources using the [Source N] format if the information is explicitly found in the provided context.
2. If no context is provided, answer using internal knowledge but do not use citations.


Context:
{context if context else "[No relevant documents found]"}

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
