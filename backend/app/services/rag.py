from typing import List, Dict, Optional
from uuid import UUID
import openai
import os
from sqlmodel import Session, select, col
from sqlalchemy import func, text
from app.models import DocumentChunk, Document, ChatMessage
from app.database import engine

class RAGService:
    """Service for Retrieval-Augmented Generation using Groq (OpenAI-compatible)"""
    
    def __init__(self):
        # Configure for Groq
        self.client = openai.OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for user query
        
        Note: Groq doesn't support embeddings yet, using fallback
        """
        # Fallback embedding (should match ingestion)
        import hashlib
        text_hash = hashlib.md5(query.encode()).hexdigest()
        fake_embedding = [float(int(text_hash[i:i+2], 16)) / 255.0 for i in range(0, 32, 1)]
        fake_embedding = fake_embedding * 48
        return fake_embedding[:1536]
    
    def vector_search(
        self,
        query_embedding: List[float],
        user_id: UUID,
        document_ids: Optional[List[UUID]] = None,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Perform vector similarity search
        
        CRITICAL: Ensures user can only access their own documents (security check)
        """
        with Session(engine) as session:
            # Build query with vector similarity
            embedding_str = f"[{','.join(map(str, query_embedding))}]"
            
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
                    1 - (dc.embedding <=> '{embedding_str}'::vector) as similarity
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.user_id = '{str(user_id)}'
                  AND d.is_deleted = false
                  AND 1 - (dc.embedding <=> '{embedding_str}'::vector) >= {threshold}
                ORDER BY similarity DESC
                LIMIT {limit}
            """
            
            results = session.execute(text(query_sql)).fetchall()
            
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
                    "similarity": float(row[8])
                })
            
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
        model: str = "llama-3.1-70b-versatile",  # Groq's fast model
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
1. Only use information from the provided context to answer questions
2. If the context doesn't contain relevant information, say so
3. Always cite your sources using the format [Source N] when referencing information
4. Be precise with numbers and financial data
5. Handle personally identifiable information (PII) carefully
6. If you're unsure, acknowledge the uncertainty

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
        model: str = "llama-3.1-70b-versatile"
    ):
        """
        Generate streaming response (for real-time UI updates)
        
        Yields:
            Response chunks as they're generated
        """
        prompt = f"""You are a knowledgeable finance expert assistant. 
Your role is to provide accurate, helpful financial advice based on the provided context.

CRITICAL RULES:
1. Only use information from the provided context
2. Always cite sources using [Source N] format
3. Be precise with financial data
4. Handle PII carefully

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
