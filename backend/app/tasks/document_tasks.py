from app.celery_app import celery_app
from app.services.ingestion import IngestionService
from uuid import UUID

@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    """
    Celery task to process uploaded document
    
    Steps:
    1. Extract text from document
    2. Chunk the text
    3. Generate embeddings
    4. Save chunks to database
    5. Update document status
    
    Args:
        document_id: UUID of the document to process
    """
    try:
        ingestion_service = IngestionService()
        doc_uuid = UUID(document_id)
        ingestion_service.process_document(doc_uuid)
        return {"status": "success", "document_id": document_id}
    
    except Exception as e:
        # Retry on failure
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
