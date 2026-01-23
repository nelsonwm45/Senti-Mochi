from sqlmodel import Session, select
from app.database import engine
from app.models import NewsArticle, NewsChunk, Company
from app.services.embedding_service import embedding_service
from uuid import uuid4
from datetime import datetime
import time

def verify():
    with Session(engine) as session:
        # Create dummy company
        suffix = str(uuid4())[:8]
        company = Company(name=f"VectorTest Corp {suffix}", ticker=f"VEC{suffix}")
        session.add(company)
        session.commit()
        session.refresh(company)
        print(f"Created company: {company.name}")

        # Create dummy article about "Cybersecurity Breach"
        content = """
        VectorTest Corp suffered a major cybersecurity breach on Sunday. 
        Hackers accessed the customer database and stole 1 million records.
        The CTO has resigned immediately. 
        Stock price fell by 15% in pre-market trading.
        Analysts downgrade the stock to SELL due to reputational damage.
        """
        
        article = NewsArticle(
            company_id=company.id,
            source="manual_test",
            native_id=f"test-{suffix}",
            title="Massive Data Breach at VectorTest Corp",
            url="http://test.com",
            content=content,
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        print(f"Created article: {article.title} (ID: {article.id})")

        # TRANSFORM!
        print("Triggering vectorization task logic (synchronously)...")
        from app.tasks.vector_tasks import vectorize_article_task
        vectorize_article_task(str(article.id))
        
        # Verify Chunks
        chunks = session.exec(select(NewsChunk).where(NewsChunk.news_id == article.id)).all()
        print(f"Generated {len(chunks)} chunks.")
        
        if not chunks:
            print("FAILURE: No chunks created.")
            return

        print(f"Chunk 0 content: {chunks[0].content[:50]}...")
        if chunks[0].embedding is not None:
             print(f"Chunk 0 embedding size: {len(chunks[0].embedding)}")
        else:
             print("FAILURE: No embedding found.")

        # Test Semantic Search
        print("\nTesting Semantic Search for 'hacks'...")
        query_vec = embedding_service.generate_embeddings(["hacks database stole"])[0]
        
        vector_stmt = (
            select(NewsChunk)
            .join(NewsArticle)
            .where(NewsArticle.company_id == company.id)
            .order_by(NewsChunk.embedding.l2_distance(query_vec))
            .limit(1)
        )
        
        result = session.exec(vector_stmt).first()
        if result:
            print(f"Found match: {result.content}")
            print("SUCCESS: Vector search works!")
        else:
            print("FAILURE: Vector search found nothing.")

if __name__ == "__main__":
    verify()
