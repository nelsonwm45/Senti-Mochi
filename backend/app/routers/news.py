from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, desc
from app.database import get_session
from app.models import NewsArticle, User, Watchlist, Company
from app.auth import get_current_user
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.tasks.sentiment_tasks import analyze_article_sentiment_task

router = APIRouter(prefix="/news", tags=["news"])

from sqlalchemy.orm import joinedload

# Schema for storing articles from client
class ClientNewsArticle(BaseModel):
    company_id: str
    source: str
    native_id: str
    title: str
    url: str
    published_at: str  # ISO string from frontend
    content: Optional[str] = None

@router.post("/store-articles")
def store_articles(
    articles: List[ClientNewsArticle],
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    """
    Store news articles fetched from client-side APIs.
    Used for Bursa Malaysia and other APIs that can only be called from the browser.
    """
    saved_count = 0
    
    for article_data in articles:
        try:
            # Check if article already exists
            existing = session.exec(select(NewsArticle).where(
                NewsArticle.native_id == article_data.native_id
            )).first()
            
            if existing:
                continue
            
            # Parse ISO datetime string
            try:
                published_at = datetime.fromisoformat(article_data.published_at.replace('Z', '+00:00'))
            except:
                published_at = datetime.utcnow()
            
            # Create and save article
            article = NewsArticle(
                company_id=article_data.company_id,
                source=article_data.source,
                native_id=article_data.native_id,
                title=article_data.title,
                url=article_data.url,
                published_at=published_at,
                content=article_data.content
            )
            session.add(article)
            saved_count += 1
        except Exception as e:
            print(f"Error storing article: {e}")
            continue
    
    if saved_count > 0:
        session.commit()
        
        # Trigger sentiment analysis for newly saved articles
        # Query to get the newly saved articles
        stmt = select(NewsArticle).where(
            NewsArticle.native_id.in_([
                article_data.native_id for article_data in articles
                if article_data.source.lower() != "bursa"  # Skip Bursa
            ])
        ).where(NewsArticle.analyzed_at == None)  # Only new articles
        
        newly_saved = session.exec(stmt).all()
        
        # Queue sentiment analysis tasks for each new article
        for article in newly_saved:
            analyze_article_sentiment_task.delay(str(article.id))
    
    return {"saved": saved_count, "total": len(articles)}

@router.get("/feed")
def get_news_feed(
    limit: int = 50,
    watchlist_only: bool = True,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    """
    Get news feed.
    Returns enriched articles with company info.
    """
    statement = select(NewsArticle, Company).join(Company).order_by(desc(NewsArticle.published_at))
    
    if watchlist_only:
        watchlist_stmt = select(Watchlist.company_id).where(Watchlist.user_id == user.id)
        followed_ids = session.exec(watchlist_stmt).all()
        
        if not followed_ids:
            return []
            
        statement = statement.where(NewsArticle.company_id.in_(followed_ids))
    
    statement = statement.limit(limit)
    results = session.exec(statement).all()
    
    articles = []
    for article, company in results:
        article_dict = {
            "id": str(article.id),
            "companyId": str(company.id),  # Add company ID for filtering
            "type": article.source, # Frontend expects 'type'
            "title": article.title,
            "link": article.url,
            "date": article.published_at.isoformat(),
            "timestamp": article.published_at.timestamp(),
            "company": company.name,
            "companyCode": company.ticker,
            "description": article.content,
            "source": article.source.title() # "Bursa", "Star", "Nst"
        }
        
        # Add sentiment data if available
        if article.sentiment_label:
            article_dict["sentiment"] = {
                "label": article.sentiment_label,  # "Positive", "Neutral", "Negative"
                "score": article.sentiment_score,   # -1.0 to 1.0
                "confidence": article.sentiment_confidence,  # 0.0 to 1.0
                "analyzed_at": article.analyzed_at.isoformat() if article.analyzed_at else None
            }
        
        articles.append(article_dict)
    
    return articles

@router.post("/analyze-sentiment")
def trigger_sentiment_analysis(
    limit: int = 50,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    """
    Manually trigger sentiment analysis for unanalyzed articles.
    Admin endpoint to catch up on sentiment analysis.
    """
    from app.tasks.sentiment_tasks import analyze_all_unanalyzed_articles_task
    
    # Queue the task
    task = analyze_all_unanalyzed_articles_task.delay(limit=limit)
    
    return {
        "message": f"Sentiment analysis queued for up to {limit} articles",
        "task_id": task.id
    }


@router.get("/sentiment-status/{article_id}")
def get_sentiment_status(
    article_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    """
    Get sentiment analysis status and results for an article.
    """
    article = session.get(NewsArticle, article_id)
    
    if not article:
        return {"error": "Article not found"}, 404
    
    return {
        "article_id": str(article.id),
        "analyzed": article.analyzed_at is not None,
        "sentiment": {
            "label": article.sentiment_label,
            "score": article.sentiment_score,
            "confidence": article.sentiment_confidence,
            "analyzed_at": article.analyzed_at.isoformat() if article.analyzed_at else None
        } if article.analyzed_at else None
    }