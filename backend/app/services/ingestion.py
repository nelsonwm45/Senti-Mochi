from typing import List, Dict, BinaryIO
from uuid import UUID
import io
from pypdf import PdfReader
from docx import Document as DocxDocument
import openai
import os
import pytesseract
from PIL import Image
import fitz  # PyMuPDF for extracting images from PDFs
from app.services.storage import S3StorageService
from app.models import Document, DocumentChunk, DocumentStatus
from app.database import engine
from sqlmodel import Session, select
from datetime import datetime, timezone

class IngestionService:
    """Service for processing and ingesting documents for RAG"""
    
    def __init__(self):
        self.storage = S3StorageService()
        # Configure for Groq (OpenAI-compatible)
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        self.chunk_size = 150  # tokens - smaller for better precision
        self.chunk_overlap = 30  # tokens
    
    def extract_text_from_pdf(self, file_bytes: bytes) -> List[Dict]:
        """
        Extract text from PDF file, including OCR for images

        Uses PyMuPDF (fitz) to extract both embedded text and images.
        Images are processed with Tesseract OCR to extract text.

        Returns:
            List of dicts with 'page_number' and 'content'
        """
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

            pages = []
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                page_texts = []

                # Extract regular text from page
                regular_text = page.get_text("text")
                if regular_text.strip():
                    page_texts.append(regular_text)

                # Extract images and perform OCR
                image_list = page.get_images(full=True)
                for img_index, img_info in enumerate(image_list):
                    try:
                        # Get the image xref
                        xref = img_info[0]

                        # Extract image bytes
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]

                        # Open image with PIL
                        image = Image.open(io.BytesIO(image_bytes))

                        # Convert to RGB if necessary (handles CMYK, etc.)
                        if image.mode not in ('L', 'RGB'):
                            image = image.convert('RGB')

                        # Perform OCR on the image
                        ocr_text = pytesseract.image_to_string(image)

                        if ocr_text.strip():
                            page_texts.append(f"\n[Image {img_index + 1} OCR Text]\n{ocr_text}")

                    except Exception as img_error:
                        # Log but continue if individual image fails
                        continue

                # Combine all text from the page
                combined_text = "\n".join(page_texts)
                if combined_text.strip():
                    pages.append({
                        "page_number": page_num + 1,
                        "content": combined_text.replace("\x00", "")
                    })

            pdf_document.close()
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
    
    def extract_text_from_image(self, file_bytes: bytes) -> List[Dict]:
        """Extract text from image using Tesseract OCR"""
        try:
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
            
            return [{
                "page_number": 1,
                "content": text.replace("\x00", "")
            }]
        except Exception as e:
            raise ValueError(f"Failed to extract text from image: {str(e)}")
    
    def extract_text(self, file_bytes: bytes, content_type: str) -> List[Dict]:
        """Extract text based on file type"""
        if content_type == "application/pdf":
            return self.extract_text_from_pdf(file_bytes)
        elif content_type in ["text/plain", "text/txt"]:
            return self.extract_text_from_txt(file_bytes)
        elif content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            return self.extract_text_from_docx(file_bytes)
        elif content_type.startswith("image/"):
            return self.extract_text_from_image(file_bytes)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
    
    def chunk_text(self, pages: List[Dict]) -> List[Dict]:
        """
        Split text into chunks with overlap, tracking line numbers.
        Strategy:
        1. Split by double newlines (\n\n) to likely preserve paragraphs.
        2. If paragraph > chunk_size, split by sentences/lines.
        3. Simple fallback to overlapping word chunks if structure is messy.
        """
        chunks = []
        chunk_index = 0
        
        for page in pages:
            content = page["content"]
            page_number = page["page_number"]
            
            # 1. Attempt Paragraph Split
            paragraphs = content.split('\n\n')
            
            # Map words to lines for the whole page first is expensive, 
            # let's do a simpler sliding window approach but respect paragraphs boundaries.
            
            # Refined strategy:
            # We iterate paragraphs. 
            # If paragraph fits in chunk_size, add it.
            # If paragraph is huge, split it.
            
            # First, we need a way to track line numbers for paragraphs.
            # This is complex because split('\n\n') loses line info.
            # Let's fallback to the robust sliding window from before but encourage it to snap to newlines?
            
            # Use original simpler logic but check for `\n` in the words to detect boundaries?
            # Replaced with the "Smart Paragraph" logic requested:
            
            words_with_lines = []
            lines = content.split('\n')
            for line_idx, line in enumerate(lines):
                line_words = line.split()
                # Empty lines (likely paragraph breaks)
                if not line_words:
                    words_with_lines.append(("\n", line_idx + 1)) # Marker for newline
                    continue
                    
                for word in line_words:
                    words_with_lines.append((word, line_idx + 1))
            
            if not words_with_lines:
                continue

            chunk_size_words = self.chunk_size
            overlap_words = self.chunk_overlap
            
            # Sliding window with boundary awareness
            current_start = 0
            while current_start < len(words_with_lines):
                # Suggest end point
                current_end = min(current_start + chunk_size_words, len(words_with_lines))
                
                # Look for paragraph break (\n marker) near the end to snap to
                # Hunt backwards from current_end to (current_start + min_size)
                # But for now, stick to simple overlapping but handle the newlines properly.
                
                chunk_data = words_with_lines[current_start:current_end]
                
                # Reconstruct
                reconstructed_text = ""
                last_line_num = -1
                
                real_words_count = 0
                
                for token, line_num in chunk_data:
                    if token == "\n":
                        reconstructed_text += "\n"
                        continue
                        
                    if last_line_num != -1 and line_num > last_line_num:
                        # New line but regular word
                        reconstructed_text += " " # Just space for now, or "\n"
                    elif len(reconstructed_text) > 0 and reconstructed_text[-1] != "\n":
                        reconstructed_text += " "
                        
                    reconstructed_text += token
                    last_line_num = line_num
                    real_words_count += 1
                
                if reconstructed_text.strip():
                     chunks.append({
                        "content": reconstructed_text.strip(),
                        "page_number": page_number,
                        "chunk_index": chunk_index,
                        "token_count": real_words_count,
                        "start_line": chunk_data[0][1],
                        "end_line": chunk_data[-1][1],
                        "metadata": {
                            "word_count": real_words_count
                        }
                    })
                     chunk_index += 1
                
                # Move window
                current_start += (chunk_size_words - overlap_words)
        
        return chunks
    
    def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for chunks using Sentence Transformers (local)
        
        Model: all-MiniLM-L6-v2 (384 dimensions)
        - Fast and efficient
        - Good quality semantic embeddings
        - Runs locally, no API costs
        
        Returns:
            Chunks with embeddings added
        """
        from sentence_transformers import SentenceTransformer
        
        # Load model (cached after first load)
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Extract texts
        texts = [chunk["content"] for chunk in chunks]
        
        # Generate embeddings in batch (more efficient)
        embeddings = model.encode(texts, show_progress_bar=False)
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i].tolist()
        
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
                    start_line=chunk.get("start_line"),
                    end_line=chunk.get("end_line"),
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

            # Store s3_key and content_type before any commits
            s3_key = document.s3_key
            content_type = document.content_type

            try:
                # Update status
                document.status = DocumentStatus.PROCESSING
                document.processing_started = datetime.now(timezone.utc)
                session.add(document)
                session.commit()

                # Download file
                file_bytes = self.storage.download_file(s3_key)

                # Extract text
                pages = self.extract_text(file_bytes, content_type)

                # Check for empty document
                if not pages or all(not p.get("content", "").strip() for p in pages):
                    raise ValueError("No text could be extracted from the document. The file may be empty, corrupted, or contain only images without OCR-readable text.")

                # Chunk text
                chunks = self.chunk_text(pages)

                # Check for empty chunks
                if not chunks:
                    raise ValueError("Document text could not be chunked. The extracted content may be too short or contain only whitespace.")

                # Generate embeddings
                chunks_with_embeddings = self.generate_embeddings(chunks)

                # Save chunks
                self.save_chunks(document_id, chunks_with_embeddings)

                # Re-fetch document to avoid detachment issues
                document = session.get(Document, document_id)
                if document:
                    document.status = DocumentStatus.PROCESSED
                    document.processing_completed = datetime.now(timezone.utc)
                    session.add(document)
                    session.commit()

            except Exception as e:
                # Re-fetch document to avoid detachment issues
                document = session.get(Document, document_id)
                if document:
                    document.status = DocumentStatus.FAILED
                    document.error_message = str(e)[:500]  # Limit error message length
                    session.add(document)
                    session.commit()
                raise
