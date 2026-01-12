from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.database import get_session
from app.models import NewsArticle, SentimentAnalysis, Company
from app.auth import get_current_user, User

router = APIRouter(prefix="/news", tags=["news"])

class NewsItem(BaseModel):
    id: UUID
    title: str
    source: str
    url: str
    published_at: str
    sentiment: str
    summary: Optional[str] = None
    content_preview: Optional[str] = None
    company_ticker: Optional[str] = None

@router.get("/", response_model=List[NewsItem])
def get_all_news(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get global news feed"""
    query = select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit)
    articles = session.exec(query).all()

    results = []
    for article in articles:
        # Fetch sentiment
        sentiment_q = select(SentimentAnalysis).where(SentimentAnalysis.news_article_id == article.id)
        sentiment = session.exec(sentiment_q).first()

        # Fetch company ticker if linked
        ticker = None
        if article.company_id:
            company = session.get(Company, article.company_id)
            if company:
                ticker = company.ticker

        # Get first 50 words of content as preview
        content_preview = None
        text_source = article.article_content if article.article_content else article.content
        if text_source:
            words = text_source.split()[:50]
            content_preview = ' '.join(words) + ('...' if len(text_source.split()) > 50 else '')

        results.append(NewsItem(
            id=article.id,
            title=article.title,
            source=article.source_name,
            url=article.url,
            published_at=article.published_at.isoformat(),
            sentiment=sentiment.score if sentiment else "Neutral",
            summary=article.summary,
            content_preview=content_preview,
            company_ticker=ticker
        ))
    return results
