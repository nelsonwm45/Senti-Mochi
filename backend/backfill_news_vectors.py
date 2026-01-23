from sqlmodel import Session, select
from app.database import engine
from app.models import NewsArticle, NewsChunk
from app.tasks.vector_tasks import vectorize_article_task
import time

def backfill():
    with Session(engine) as session:
        # Find articles without chunks
        # Get all article IDs
        all_articles = session.exec(select(NewsArticle)).all()
        # Get IDs with chunks
        chunked_ids = session.exec(select(NewsChunk.news_id).distinct()).all()
        chunked_ids_set = set(chunked_ids)
        
        to_process = [a for a in all_articles if a.id not in chunked_ids_set]
        
        print(f"Found {len(to_process)} articles needing vectorization.")
        
        for i, article in enumerate(to_process):
            print(f"[{i+1}/{len(to_process)}] Processing: {article.title[:50]}...")
            if not article.content:
                print("  Skipping (no content)")
                continue
                
            try:
                # Run synchronously for backfill script
                vectorize_article_task(str(article.id))
            except Exception as e:
                print(f"  Error: {e}")

    print("Backfill complete!")

if __name__ == "__main__":
    backfill()
