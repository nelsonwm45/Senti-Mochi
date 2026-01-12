from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID

from app.database import get_session
from app.models import Company, NewsArticle, Filing, FinancialRatio, SentimentAnalysis
from app.auth import get_current_user, User
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])

# Response Models
class CompanyOverview(BaseModel):
    id: UUID
    name: str
    ticker: str
    sector: Optional[str]
    market_cap: Optional[float]
    summary: Optional[str]
    recent_news: List[dict]
    recent_filings: List[dict]
    financial_ratios: List[dict]

@router.get("/{company_id}/overview", response_model=CompanyOverview)
async def get_company_overview(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Company 360 View: Aggregates all data for a specific company.
    """
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Fetch News (limit 5)
    news_query = select(NewsArticle).where(NewsArticle.company_id == company_id).order_by(NewsArticle.published_at.desc()).limit(5)
    news_articles = session.exec(news_query).all()
    
    # Format News with Sentiment
    news_data = []
    for article in news_articles:
        # Fetch sentiment if exists (optimization: could join)
        sentiment_q = select(SentimentAnalysis).where(SentimentAnalysis.news_article_id == article.id)
        sentiment_res = session.exec(sentiment_q).first()
        
        news_data.append({
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "published_at": article.published_at,
            "sentiment": sentiment_res.score if sentiment_res else "Neutral"
        })

    # Fetch Filings (limit 5)
    filings_query = select(Filing).where(Filing.company_id == company_id).order_by(Filing.publication_date.desc()).limit(5)
    filings = session.exec(filings_query).all()
    filings_data = [
        {
            "id": f.id,
            "type": f.type,
            "date": f.publication_date,
            "summary": f.content_summary[:200] if f.content_summary else ""
        }
        for f in filings
    ]

    # Fetch Ratios
    ratios_query = select(FinancialRatio).where(FinancialRatio.company_id == company_id).order_by(FinancialRatio.created_at.desc())
    ratios = session.exec(ratios_query).all()
    ratios_data = [
        {
            "name": r.ratio_name,
            "value": r.value,
            "period": r.period
        }
        for r in ratios
    ]

    return CompanyOverview(
        id=company.id,
        name=company.name,
        ticker=company.ticker,
        sector=company.sector,
        market_cap=company.market_cap,
        summary=company.summary,
        recent_news=news_data,
        recent_filings=filings_data,
        financial_ratios=ratios_data
    )
