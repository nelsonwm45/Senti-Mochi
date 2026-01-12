from app.services.ingestion import IngestionService
from app.services.rag import RAGService
from uuid import uuid4

def verify_phase4():
    print("--- Verifying Text Chunking ---")
    ingest = IngestionService()
    text_content = "This is Paragraph 1.\n\nThis is Paragraph 2. It is longer and contains more details about financial results.\n\nThis is Paragraph 3."
    pages = [{"content": text_content, "page_number": 1}]
    chunks = ingest.chunk_text(pages)
    print(f"Text separated by double newlines into {len(chunks)} chunks.")
    for i, c in enumerate(chunks):
        print(f"Chunk {i}: {c['content'][:30]}...")

    print("\n--- Verifying RAG Search with Filters (Dry Run) ---")
    rag = RAGService()
    # Mocking embedding to avoid API call
    mock_embedding = [0.1] * 384
    
    try:
        # This will fail to find anything but verifies the SQL generation doesn't crash
        results = rag.vector_search(
            query_embedding=mock_embedding,
            user_id=uuid4(),
            filters={"company_id": str(uuid4()), "type": "ANNUAL_REPORT"}
        )
        print("Vector search with filters executed without SQL error.")
    except Exception as e:
        print(f"Vector search failed: {e}")

if __name__ == "__main__":
    verify_phase4()
