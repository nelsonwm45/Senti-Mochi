from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, desc
from app.database import get_session
from app.models import NewsArticle, User, Watchlist, Company
from app.auth import get_current_user
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/news", tags=["news"])

from sqlalchemy.orm import joinedload

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
        articles.append({
            "id": str(article.id),
            "type": article.source, # Frontend expects 'type'
            "title": article.title,
            "link": article.url,
            "date": article.published_at.isoformat(),
            "timestamp": article.published_at.timestamp(),
            "company": company.name,
            "companyCode": company.ticker,
            "description": article.content,
            "source": article.source.title() # "Bursa", "Star", "Nst"
        })
    
    return articles
