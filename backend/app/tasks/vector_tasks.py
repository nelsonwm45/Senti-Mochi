from app.celery_app import celery_app
from sqlmodel import Session, select
from app.database import engine
from app.models import NewsArticle, NewsChunk
from app.services.embedding_service import embedding_service

@celery_app.task(name="vectorize_article_task")
def vectorize_article_task(article_id: str):
    """
    Async task to chunk news article and generate embeddings.
    Checks if chunks already exist to avoid duplication.
    """
    print(f"[VECTOR_TASK] Starting vectorization for article {article_id}")
    
    with Session(engine) as session:
        article = session.get(NewsArticle, article_id)
        if not article or not article.content:
            print(f"[VECTOR_TASK] Article not found or empty: {article_id}")
            return

        # Check existing chunks
        existing_chunks = session.exec(select(NewsChunk).where(NewsChunk.news_id == article.id)).first()
        if existing_chunks:
             print(f"[VECTOR_TASK] Chunks already exist for {article_id}. Skipping.")
             return

        # Chunking Logic (Sliding Window)
        words = article.content.split()
        chunk_size = 200
        overlap = 20
        
        if not words:
            return

        chunks_data = []
        chunk_index = 0
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i : i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunks_data.append({
                "text": chunk_text,
                "index": chunk_index
            })
            chunk_index += 1
        
        # Generate Embeddings
        texts = [c["text"] for c in chunks_data]
        try:
            embeddings = embedding_service.generate_embeddings(texts)
            
            # Save Chunks
            for i, data in enumerate(chunks_data):
                chunk = NewsChunk(
                    news_id=article.id,
                    content=data["text"],
                    chunk_index=data["index"],
                    embedding=embeddings[i]
                )
                session.add(chunk)
            
            session.commit()
            print(f"[VECTOR_TASK] Successfully created {len(texts)} vector chunks for {article_id}")
            
        except Exception as e:
            print(f"[VECTOR_TASK] Error generating embeddings: {e}")
