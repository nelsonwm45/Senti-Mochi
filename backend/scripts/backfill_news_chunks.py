
import sys
import os
from pathlib import Path

# Add backend directory to path so we can import app modules
backend_path = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_path))

from sqlmodel import Session, select
from app.database import engine
from app.models import NewsArticle, NewsChunk

def backfill_chunks():
    print("Starting NewsChunk backfill...")
    with Session(engine) as session:
        # Get all articles
        statement = select(NewsArticle)
        articles = session.exec(statement).all()
        
        count = 0
        skipped = 0
        
        for article in articles:
            # Check if likely already chunked (optimization)
            # For now, just simplistic check or delete old chunks? 
            # Better to check if chunks exist
            chunk_check = select(NewsChunk).where(NewsChunk.news_id == article.id)
            existing = session.exec(chunk_check).first()
            if existing:
                skipped += 1
                continue
            
            if not article.content:
                continue

            # Split by double newline (paragraphs)
            paragraphs = [p.strip() for p in article.content.split('\n\n') if p.strip()]
            
            for index, p in enumerate(paragraphs):
                chunk = NewsChunk(
                    news_id=article.id,
                    content=p,
                    chunk_index=index
                )
                session.add(chunk)
            
            count += 1
            if count % 10 == 0:
                print(f"Processed {count} articles...")
        
        session.commit()
        print(f"Backfill complete! Processed {count} articles. Skipped {skipped} already chunked.")

if __name__ == "__main__":
    backfill_chunks()
