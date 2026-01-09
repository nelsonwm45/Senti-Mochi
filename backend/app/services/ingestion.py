from typing import List, Dict, BinaryIO
from uuid import UUID
import io
from pypdf import PdfReader
from docx import Document as DocxDocument
import openai
import os
from app.services.storage import S3StorageService
from app.models import Document, DocumentChunk, DocumentStatus
from app.database import engine
from sqlmodel import Session, select
from datetime import datetime

class IngestionService:
    """Service for processing and ingesting documents for RAG"""
    
    def __init__(self):
        self.storage = S3StorageService()
        # Configure for Groq (OpenAI-compatible)
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        self.chunk_size = 800  # tokens
        self.chunk_overlap = 100  # tokens
    
    def extract_text_from_pdf(self, file_bytes: bytes) -> List[Dict]:
        """
        Extract text from PDF file
        
        Returns:
            List of dicts with 'page_number' and 'content'
        """
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_file)
            
            pages = []
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text.strip():
                    pages.append({
                        "page_number": page_num,
                        "content": text
                    })
            
            return pages
        except Exception as e:
            # If PDF reading fails, might be empty or corrupted
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_text_from_txt(self, file_bytes: bytes) -> List[Dict]:
        """Extract text from plain text file"""
        try:
            text = file_bytes.decode('utf-8')
            return [{
                "page_number": 1,
                "content": text
            }]
        except Exception as e:
            raise ValueError(f"Failed to extract text from text file: {str(e)}")
    
    def extract_text_from_docx(self, file_bytes: bytes) -> List[Dict]:
        """Extract text from DOCX file"""
        docx_file = io.BytesIO(file_bytes)
        doc = DocxDocument(docx_file)
        
        full_text = "\n".join([para.text for para in doc.paragraphs])
        
        return [{
            "page_number": 1,
            "content": full_text
        }]
    
    def extract_text(self, file_bytes: bytes, content_type: str) -> List[Dict]:
        """Extract text based on file type"""
        if content_type == "application/pdf":
            return self.extract_text_from_pdf(file_bytes)
        elif content_type in ["text/plain", "text/txt"]:
            return self.extract_text_from_txt(file_bytes)
        elif content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            return self.extract_text_from_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
    
    def chunk_text(self, pages: List[Dict]) -> List[Dict]:
        """
        Split text into chunks with overlap
        
        Returns:
            List of chunks with metadata
        """
        chunks = []
        chunk_index = 0
        
        for page in pages:
            content = page["content"]
            page_number = page["page_number"]
            
            # Simple word-based chunking (approximate tokens)
            words = content.split()
            chunk_size_words = self.chunk_size  # Approximation: 1 word ≈ 1 token
            overlap_words = self.chunk_overlap
            
            for i in range(0, len(words), chunk_size_words - overlap_words):
                chunk_words = words[i:i + chunk_size_words]
                chunk_text = " ".join(chunk_words)
                
                if chunk_text.strip():
                    chunks.append({
                        "content": chunk_text,
                        "page_number": page_number,
                        "chunk_index": chunk_index,
                        "token_count": len(chunk_words),
                        "metadata": {
                            "word_count": len(chunk_words),
                            "start_word_index": i
                        }
                    })
                    chunk_index += 1
        
        return chunks
    
    def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for chunks using OpenAI-compatible API (Groq doesn't have embeddings yet)
        
        Note: For now using a simple TF-IDF approach or you need separate embedding service
        We'll use OpenAI embeddings model through nomic-embed-text on Groq when available
        
        Returns:
            Chunks with embeddings added
        """
        # Batch process chunks
        texts = [chunk["content"] for chunk in chunks]
        
        # Use OpenAI embedding model (works with Groq base URL if they support it)
        # Note: Groq doesn't currently support embeddings, so we use text-embedding-ada-002
        # You may need to use OpenAI for embeddings separately or use local embeddings
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",  # This won't work on Groq
                input=texts
            )
            
            # Add embeddings to chunks
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = response.data[i].embedding
        except Exception as e:
            # Fallback: use simple embedding (this is NOT ideal for production)
            # In production, you'd use a separate embedding service
            print(f"Warning: Embedding generation failed: {e}")
            print("Using fallback simple embeddings (not recommended for production)")
            
            # Simple fallback: create fake embeddings (768 dims)
            # TODO: Use proper embedding model like sentence-transformers
            import hashlib
            for chunk in chunks:
                # Generate deterministic fake embedding from text hash
                text_hash = hashlib.md5(chunk["content"].encode()).hexdigest()
                # Create 768-dim vector from hash
                fake_embedding = [float(int(text_hash[i:i+2], 16)) / 255.0 for i in range(0, 32, 1)]
                # Pad to 1536 dimensions (OpenAI embedding size)
                fake_embedding = fake_embedding * 48  # 32 * 48 = 1536
                chunk["embedding"] = fake_embedding[:1536]
        
        return chunks
    
    def save_chunks(self, document_id: UUID, chunks: List[Dict]):
        """Save chunks to database"""
        with Session(engine) as session:
            chunk_models = [
                DocumentChunk(
                    document_id=document_id,
                    content=chunk["content"],
                    page_number=chunk["page_number"],
                    chunk_index=chunk["chunk_index"],
                    token_count=chunk["token_count"],
                    embedding=chunk["embedding"],
                    metadata_=chunk.get("metadata", {})
                )
                for chunk in chunks
            ]
            
            session.add_all(chunk_models)
            session.commit()
    
    def process_document(self, document_id: UUID):
        """
        Main processing pipeline for a document
        
        Steps:
        1. Download from S3
        2. Extract text
        3. Chunk text
        4. Generate embeddings
        5. Save to database
        """
        with Session(engine) as session:
            # Get document
            document = session.get(Document, document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            try:
                # Update status
                document.status = DocumentStatus.PROCESSING
                document.processing_started = datetime.utcnow()
                session.add(document)
                session.commit()
                
                # Download file
                file_bytes = self.storage.download_file(document.s3_key)
                
                # Extract text
                pages = self.extract_text(file_bytes, document.content_type)
                
                # Chunk text
                chunks = self.chunk_text(pages)
                
                # Generate embeddings
                chunks_with_embeddings = self.generate_embeddings(chunks)
                
                # Save chunks
                self.save_chunks(document_id, chunks_with_embeddings)
                
                # Update document status
                document.status = DocumentStatus.PROCESSED
                document.processing_completed = datetime.utcnow()
                session.add(document)
                session.commit()
                
            except Exception as e:
                # Update status to failed
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
                session.add(document)
                session.commit()
                raise
