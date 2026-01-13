"""
Celery tasks for enriching news articles with full content
"""
from app.celery_app import celery_app
from app.services.article_fetcher import article_fetcher_service
from sqlmodel import Session, select
from app.database import engine
from app.models import NewsArticle
from datetime import datetime

@celery_app.task(name="enrich_article_content_task")
def enrich_article_content_task(article_id: str):
    """
    Fetch full article content for a news article using newspaper3k.
    This enriches articles that only have summaries/descriptions with full text.
    """
    with Session(engine) as session:
        article = session.get(NewsArticle, article_id)
        
        if not article:
            print(f"[ENRICH] Article {article_id} not found")
            return
        
        if not article.url:
            print(f"[ENRICH] Article {article_id} has no URL")
            return
        
        # Skip Bursa announcements (they require authentication/special handling)
        if article.source.lower() == 'bursa':
            print(f"[ENRICH] Skipping Bursa article (special handling needed)")
            return
        
        # Check if content is already substantial (>500 chars)
        if article.content and len(article.content) > 500:
            print(f"[ENRICH] Article {article_id} already has substantial content ({len(article.content)} chars)")
            return
        
        print(f"[ENRICH] Fetching full content for article {article_id} from {article.url}")
        
        # Fetch full article content
        full_content = article_fetcher_service.fetch_article_content(article.url)
        
        if full_content:
            # Update the article with full content
            article.content = full_content
            article.updated_at = datetime.utcnow()
            session.add(article)
            session.commit()
            
            print(f"[ENRICH] Successfully enriched article {article_id} with {len(full_content)} chars of content")
            
            # Now trigger sentiment analysis on the FULL content
            from app.tasks.sentiment_tasks import analyze_article_sentiment_task
            analyze_article_sentiment_task.delay(article_id)
            print(f"[ENRICH] Queued sentiment analysis for enriched article {article_id}")
            
            return {"status": "success", "content_length": len(full_content)}
        else:
            print(f"[ENRICH] Failed to fetch content for article {article_id}")
            return {"status": "failed", "reason": "Could not extract content"}


@celery_app.task(name="enrich_all_articles_task")
def enrich_all_articles_task(limit: int = 50):
    """
    Enrich multiple articles with full content.
    Processes articles that have short content (<500 chars) or no content.
    """
    with Session(engine) as session:
        # Find articles that need enrichment (excluding Bursa)
        stmt = select(NewsArticle).where(
            NewsArticle.source != 'bursa'
        ).order_by(NewsArticle.published_at.desc()).limit(limit)
        
        articles = session.exec(stmt).all()
        
        enriched_count = 0
        for article in articles:
            # Skip if already has substantial content
            if article.content and len(article.content) > 500:
                continue
            
            # Queue individual enrichment task
            enrich_article_content_task.delay(str(article.id))
            enriched_count += 1
        
        print(f"[ENRICH] Queued {enriched_count} articles for content enrichment")
        return {"queued": enriched_count}
