from typing import List, Dict, Optional
from uuid import UUID
import openai
import os
from sqlmodel import Session, select, col
from sqlalchemy import func, text
from app.models import DocumentChunk, Document, ChatMessage
from app.database import engine

class RAGService:
    """Service for Retrieval-Augmented Generation"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for user query"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=[query]
        )
        return response.data[0].embedding
    
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
        
        Args:
            query_embedding: Query vector embedding
            user_id: Current user ID (for security filtering)
            document_ids: Optional filter by specific documents
            limit: Max number of results
            threshold: Minimum similarity score (0-1)
            
        Returns:
            List of matching chunks with metadata
        """
        with Session(engine) as session:
            # Build query with vector similarity
            # Using cosine distance (1 - cosine_similarity) from pgvector
            embedding_str = f"[{','.join(map(str, query_embedding))}]"
            
            # Base query with security check - MUST filter by user_id
            query = text("""
                SELECT 
                    dc.id,
                    dc.document_id,
                    dc.content,
                    dc.page_number,
                    dc.chunk_index,
                    dc.metadata_,
                    d.filename,
                    d.user_id,
                    1 - (dc.embedding <=> :embedding::vector) as similarity
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.user_id = :user_id
                  AND d.is_deleted = false
                  AND 1 - (dc.embedding <=> :embedding::vector) >= :threshold
            """)
            
            params = {
                "embedding": embedding_str,
                "user_id": str(user_id),
                "threshold": threshold
            }
            
            # Add document filter if provided
            if document_ids:
                query = text(str(query) + " AND d.id = ANY(:document_ids)")
                params["document_ids"] = [str(doc_id) for doc_id in document_ids]
            
            query = text(str(query) + " ORDER BY similarity DESC LIMIT :limit")
            params["limit"] = limit
            
            results = session.execute(query, params).fetchall()
            
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
        """
        Build context string from retrieved chunks
        
        Args:
            chunks: List of retrieved chunks
            max_tokens: Maximum tokens for context
            
        Returns:
            Formatted context string
        """
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
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7
    ) -> Dict:
        """
        Generate response using LLM with context
        
        Returns:
            Dict with 'response' and extracted 'citations'
        """
        system_prompt = """You are a knowledgeable finance expert assistant. 
Your role is to provide accurate, helpful financial advice based on the provided context.

CRITICAL RULES:
1. Only use information from the provided context to answer questions
2. If the context doesn't contain relevant information, say so
3. Always cite your sources using the format [Source N] when referencing information
4. Be precise with numbers and financial data
5. Handle personally identifiable information (PII) carefully
6. If you're unsure, acknowledge the uncertainty

Format your citations as: [Source 1], [Source 2], etc."""
        
        user_message = f"""Context:\n{context}\n\n---\n\nUser Question: {query}"""
        
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature
        )
        
        answer = response.choices[0].message.content
        
        # Extract citations (simple regex to find [Source N])
        import re
        citations = re.findall(r'\[Source (\d+)\]', answer)
        
        return {
            "response": answer,
            "citations": list(set(citations)),  # Unique citations
            "model": model,
            "tokens_used": response.usage.total_tokens
        }
    
    async def generate_response_stream(
        self,
        query: str,
        context: str,
        model: str = "gpt-3.5-turbo"
    ):
        """
        Generate streaming response (for real-time UI updates)
        
        Yields:
            Response chunks as they're generated
        """
        system_prompt = """You are a knowledgeable finance expert assistant. 
Your role is to provide accurate, helpful financial advice based on the provided context.

CRITICAL RULES:
1. Only use information from the provided context
2. Always cite sources using [Source N] format
3. Be precise with financial data
4. Handle PII carefully

Format citations as: [Source 1], [Source 2], etc."""
        
        user_message = f"""Context:\n{context}\n\n---\n\nUser Question: {query}"""
        
        stream = self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
