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
        # Configure for Groq
        self.groq_client = openai.OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        # Configure for Cerebras
        self.cerebras_client = openai.OpenAI(
            api_key=os.getenv("CEREBRAS_API_KEY"),
            base_url="https://api.cerebras.ai/v1"
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
                # STRICT mode: Only get docs for this specific company. Do not include global (NULL) docs
                # unless explicitly requested. Ideally, common docs should be handled separately.
                # For now, we STRICTLY filter to avoid "AMMB in Maybank" contamination.
                # ALSO: Exclude deleted documents.
                company_filter = f"AND d.company_id IN ({ids_str}) AND d.is_deleted = false"

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
                    1 - (dc.embedding <=> '{embedding_str}'::vector) as similarity,
                    dc.start_line,
                    dc.end_line,
                    d.company_id
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
                # INTEGRITY CHECK: Verify company_id (from JOIN) matches requested company_ids
                doc_company_id = row[11] # 12th column (index 11) is d.company_id
                
                # If we are strictly filtering by company, verify logic
                if company_ids:
                    allowed_ids = [str(cid) for cid in company_ids]
                    if doc_company_id and str(doc_company_id) not in allowed_ids:
                         print(f"WARNING: Data Integrity Mismatch! Skipped chunk {row[0]} for company {doc_company_id} (Expected in {allowed_ids})")
                         continue

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
                    "end_line": row[10],
                    # Construct URL for frontend redirection
                    "url": f"/api/v1/documents/{row[1]}/download"
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

    def vector_search_news(
        self, 
        query_embedding: List[float], 
        company_id: UUID, 
        session: Session, 
        limit: int = 5
    ) -> List[Dict]:
        """
        Perform semantic search on News Chunks
        """
        from app.models import NewsChunk, NewsArticle
        
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        query_sql = f"""
            SELECT 
                nc.id,
                nc.news_id,
                nc.content,
                nc.chunk_index,
                1 - (nc.embedding <=> '{embedding_str}'::vector) as similarity,
                na.title,
                na.published_at,
                na.source,
                na.url
            FROM news_chunks nc
            JOIN news_articles na ON nc.news_id = na.id
            WHERE na.company_id = '{str(company_id)}'
            ORDER BY similarity DESC
            LIMIT {limit}
        """
        
        results = session.exec(text(query_sql)).fetchall()
        
        chunks = []
        for row in results:
            # INTEGRITY CHECK: Verify company_id (joined table) matches requested company_id
            # Although the SQL WHERE clause handles this, double-checking prevents subtle bugs
            # We don't have the company_id in the SELECT, but we trust the query for now.
            # If we wanted to be paranoid, we'd add 'na.company_id' to SELECT.
            
            chunks.append({
                "id": row[0],
                "document_id": None, # Distinct type
                "content": row[2],
                "page_number": 1, 
                "chunk_index": row[3],
                "metadata": {
                    "type": "news", 
                    "company_id": str(company_id), 
                    "article_id": str(row[1]),
                    "source": row[7],
                    "published_at": row[6].strftime('%Y-%m-%d'),
                    "url": row[8]
                },
                "filename": f"News: {row[5]}",
                "similarity": float(row[4] or 0.0),
                "start_line": None,
                "end_line": None,
                "url": row[8]
            })
            
        return chunks

        return chunks

    def vector_search_reports(
        self,
        query_embedding: List[float],
        company_id: UUID,
        user_id: UUID,
        session: Session,
        limit: int = 3
    ) -> List[Dict]:
        """
        Perform semantic search on Report Chunks
        """
        from app.models import ReportChunk, AnalysisReport
        
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        query_sql = f"""
            SELECT 
                rc.id,
                rc.report_id,
                rc.content,
                rc.chunk_index,
                1 - (rc.embedding <=> '{embedding_str}'::vector) as similarity,
                rc.section_type,
                c.ticker
            FROM report_chunks rc
            JOIN analysis_reports ar ON rc.report_id = ar.id
            JOIN companies c ON ar.company_id = c.id
            WHERE ar.company_id = '{str(company_id)}'
              AND ar.user_id = '{str(user_id)}'
            ORDER BY similarity DESC
            LIMIT {limit}
        """
        
        results = session.exec(text(query_sql)).fetchall()
        
        chunks = []
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        
        for row in results:
            ticker = row[6]
            chunks.append({
                "id": row[0],
                "document_id": None,
                "content": row[2],
                "page_number": 1, 
                "chunk_index": row[3],
                "metadata": {
                    "type": "report", 
                    "company_id": str(company_id), 
                    "report_id": str(row[1]),
                    "section": row[5]
                },
                "filename": f"Analysis Report: {row[5].replace('_', ' ').title()}",
                "similarity": float(row[4] or 0.0),
                "start_line": None,
                "end_line": None,
                # Link to watchlist page with ticker param to open details
                "url": f"{frontend_url}/watchlist?ticker={ticker}"
            })
            
        return chunks

    def get_structured_chunks_for_companies(self, companies: List, session: Session, query_embedding: Optional[List[float]] = None, user_id: Optional[UUID] = None) -> List[Dict]:
        """
        Fetch structured data chunks for a specific list of companies.
        Now includes Semantic Vectors for News if query_embedding is provided.
        """
        # Lazy imports
        from app.services.finance import finance_service
        from uuid import uuid4
        
        chunks = []
        
        for company in companies:
            # 1. Fetch Financials (Split into granular chunks)
            try:
                # Get raw data directly
                fin_data = finance_service.get_financials(company.ticker)
                
                if fin_data:
                    # Helper to get latest period data
                    def get_latest(stmt_data):
                        if not stmt_data: return None, {}
                        dates = sorted(stmt_data.keys(), reverse=True)
                        if not dates: return None, {}
                        return dates[0], stmt_data[dates[0]]

                    # 1a. Key Financial Metrics (Summary)
                    key_metrics_content = f"Key Financial Metrics for {company.name} ({company.ticker}):\\n"
                    
                    # Extract key fields from various statements
                    date_inc, inc = get_latest(fin_data.get("income_statement"))
                    if date_inc:
                        for k in ["Total Revenue", "Net Income", "EBITDA", "Gross Profit", "Diluted EPS"]:
                            if k in inc: key_metrics_content += f"{k}: {inc[k]}\\n"
                            
                    date_bal, bal = get_latest(fin_data.get("balance_sheet"))
                    if date_bal:
                        for k in ["Total Assets", "Total Liabilities Net Minority Interest", "Total Equity Gross Minority Interest", "Cash And Cash Equivalents"]:
                            if k in bal: key_metrics_content += f"{k}: {bal[k]}\\n"
                            
                    chunks.append({
                        "id": uuid4(),
                        "document_id": None,
                        "content": key_metrics_content,
                        "page_number": 1,
                        "chunk_index": 0,
                        "metadata": {"type": "financials", "subtype": "key_metrics", "company": company.ticker},
                        "filename": f"Key Metrics ({company.name})",
                        "similarity": 1.0, 
                        "start_line": None,
                        "end_line": None
                    })

            except Exception as e:
                print(f"Error fetching financials chunks for {company.ticker}: {e}")
            
            # 2. Fetch News (Hybrid: Recent + Semantic)
            # 2. Fetch News (Hybrid: Recent + Semantic)
            
            # 2a. Semantic Search
            try:
                if query_embedding:
                    semantic_news = self.vector_search_news(query_embedding, company.id, session, limit=7)
                    chunks.extend(semantic_news)
            except Exception as e:
                print(f"Error fetching semantic news chunks for {company.ticker}: {e}")

            # 2b. Latest Article Baseline
            try:
                from app.models import NewsArticle
                latest_article = session.exec(
                    select(NewsArticle)
                    .where(NewsArticle.company_id == company.id)
                    .order_by(NewsArticle.published_at.desc())
                    .limit(1)
                ).first()
                
                if latest_article:
                    content_str = f"[{latest_article.published_at.strftime('%Y-%m-%d')}] {latest_article.title} (Source: {latest_article.source})"
                    if latest_article.content:
                        content_str += f"\\nSummary: {latest_article.content[:500]}..." # Truncate for brevity
                        
                    chunks.append({
                        "id": uuid4(),
                        "document_id": None,
                        "content": content_str,
                        "page_number": 1,
                        "chunk_index": 0,
                        "metadata": {"type": "news", "subtype": "latest", "company": company.ticker, "url": latest_article.url},
                        "filename": f"Latest News: {latest_article.title}",
                        "similarity": 0.9, # High priority but below perfect vector match
                        "start_line": None,
                        "end_line": None,
                        "url": latest_article.url
                    })

            except Exception as e:
                print(f"Error fetching latest news for {company.ticker}: {e}")

            # 3. Fetch Past Analysis Reports (Semantic Search)
            try:
                if query_embedding and user_id:
                    report_chunks = self.vector_search_reports(query_embedding, company.id, user_id, session, limit=3)
                    chunks.extend(report_chunks)
            except Exception as e:
                print(f"Error fetching report chunks for {company.ticker}: {e}")
                
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
        fallback_model: str = "llama-3.3-70b-versatile",  # Groq's fast model
        temperature: float = 0.7
    ) -> Dict:
        """
        Generate response using Cerebras (primary) or Groq (fallback) with context
        
        Returns:
            Dict with 'response' and extracted 'citations'
        """
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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
2. Data Extraction: If the user requests data parsing, output strictly in JSON format with no conversational filler.
3. Tone: Maintain an institutional, objective tone. Use terms like "high volatility" or "strategic alignment" instead of "exciting" or "massive."

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
            for msg in chat_history:
                if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                    messages.append({"role": msg['role'], "content": msg['content']})
        
        # Add current turn
        messages.append({"role": "user", "content": prompt})

        # Attempt Primary: Cerebras
        try:
            print(f"[RAG Service] Attempting Cerebras (llama-3.3-70b)...")
            response = self.cerebras_client.chat.completions.create(
                model="llama-3.3-70b",
                messages=messages,
                temperature=temperature,
                max_tokens=1024
            )
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None
            used_model = "llama-3.3-70b (Cerebras)"
            print(f"[RAG Service] SUCCESS (Cerebras)")
        except Exception as e:
            print(f"[RAG Service] Cerebras failed: {e}. Fallback to Groq...")
            response = self.groq_client.chat.completions.create(
                model=fallback_model,
                messages=messages,
                temperature=temperature,
                max_tokens=1024
            )
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None
            used_model = f"{fallback_model} (Groq)"
            print(f"[RAG Service] SUCCESS (Groq)")
        
        # Extract citations (simple regex to find [Source N])
        import re
        citations = re.findall(r'\[Source (\d+)\]', answer)
        
        return {
            "response": answer,
            "citations": list(set(citations)),  # Unique citations
            "model": used_model,
            "tokens_used": tokens_used
        }

    def reindex_citations(self, text: str, chunks: list[dict]) -> tuple[str, list[dict]]:
        """
        Renumber citations in the text to be sequential (1, 2, 3...) based on appearance order.
        Also reorders the chunks list to match the new numbering.
        """
        import re
        
        # Find all current citations in the text, e.g. [Source 15], [Source 2]
        # Regex: Case insensitive, allow optional text after number (e.g. [Source 15: News...])
        pattern = r'\[Source\s*(\d+).*?\]'
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        
        if not matches:
            return text, chunks
            
        # Map from Old Source Number (int) -> New Source Number (int)
        old_to_new = {}
        new_source_counter = 1
        
        # We must process matches in order of appearance
        for m in matches:
            old_num = int(m.group(1))
            if old_num not in old_to_new:
                old_to_new[old_num] = new_source_counter
                new_source_counter += 1
                
        # 1. Replace in text
        def replace_func(match):
            old_num = int(match.group(1))
            new_num = old_to_new[old_num]
            return f"[Source {new_num}]"
            
        new_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)
        
        # 2. Reorder chunks
        reordered_chunks = []
        used_indices = set()
        
        # Invert the mapping: New -> Old
        new_to_old = {v: k for k, v in old_to_new.items()}
        
        for i in range(1, new_source_counter):
            old_source_num = new_to_old[i]
            # Source Num is 1-based, Chunk Index is 0-based
            chunk_idx = old_source_num - 1
            if 0 <= chunk_idx < len(chunks):
                reordered_chunks.append(chunks[chunk_idx])
                used_indices.add(chunk_idx)
                
        # Append unused chunks at the end - REMOVED per user request
        # for i, chunk in enumerate(chunks):
        #     if i not in used_indices:
        #         reordered_chunks.append(chunk)
                
        return new_text, reordered_chunks
    
    async def generate_response_stream(
        self,
        query: str,
        context: str,
        chat_history: List[Dict] = None,
        fallback_model: str = "llama-3.3-70b-versatile"
    ):
        """
        Generate streaming response using Cerebras (primary) or Groq (fallback)
        
        Yields:
            Response chunks as they're generated
        """
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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

        # Attempt Primary: Cerebras
        try:
            print(f"[RAG Service] Attempting Streaming with Cerebras (llama-3.3-70b)...")
            stream = self.cerebras_client.chat.completions.create(
                model="llama-3.3-70b",
                messages=messages,
                stream=True,
                max_tokens=1024
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            print(f"[RAG Service] SUCCESS (Cerebras Stream)")
        except Exception as e:
            print(f"[RAG Service] Cerebras Streaming failed: {e}. Fallback to Groq...")
            stream = self.groq_client.chat.completions.create(
                model=fallback_model,
                messages=messages,
                stream=True,
                max_tokens=1024
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            print(f"[RAG Service] SUCCESS (Groq Stream)")
