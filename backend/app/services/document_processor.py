from uuid import UUID
from sqlmodel import Session
from app.database import engine
from app.models import Filing, DocumentChunk
from app.services.ingestion import IngestionService
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.ingestion_service = IngestionService()

    def process_filing(self, filing_id: UUID):
        """
        Process a Filing:
        1. Ingest the linked Document (PDF extraction + OCR + Chunking + Embedding)
        2. Calculate Confidence Score based on OCR usage / text quality
        3. Update Filing metadata if needed
        """
        with Session(engine) as session:
            filing = session.get(Filing, filing_id)
            if not filing:
                logger.error(f"Filing {filing_id} not found")
                return
            
            if not filing.document_id:
                logger.error(f"Filing {filing_id} has no linked Document")
                return

            # Reuse existing generic ingestion
            try:
                self.ingestion_service.process_document(filing.document_id)
                
                # Post-processing: Calculate Confidence Score
                confidence = self._calculate_confidence(filing.document_id, session)
                logger.info(f"Filing {filing_id} processed with Confidence Score: {confidence}")
                
                # Could save confidence to Filing model if we add a column, 
                # or just log it for now as per requirements.
                
            except Exception as e:
                logger.error(f"Error processing filing {filing_id}: {e}")
                # Filing status handling could be improved here

    def _calculate_confidence(self, document_id: UUID, session: Session) -> float:
        """
        Calculate confidence score (0.0 to 1.0)
        Logic:
        - If text contains many "OCR Text" markers, confidence might be lower (or higher if we trust OCR?)
        - If text is very short relative to file size?
        - Basic heuristic: 1.0 default, penalty for broken text patterns
        """
        chunks = session.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
        if not chunks:
            return 0.0

        total_text = " ".join([c.content for c in chunks])
        if not total_text.strip():
            return 0.0

        score = 1.0
        
        # Heuristic 1: If mostly OCR logic (based on markers inserted by IngestionService)
        ocr_count = total_text.count("[Image")
        if ocr_count > 5:
            score -= 0.1 # Slight penalty for heavy OCR reliance? 
                         # Actually modern OCR is good. Maybe penalty for short text?
        
        # Heuristic 2: Short content
        if len(total_text) < 100:
            score -= 0.5

        return max(0.0, score)
