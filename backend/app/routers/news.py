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
            
            # SMART INGESTION: Check if the article title mentions other companies
            # This fixes the issue where searching for "Maybank" returns "Bermaz Auto" news but tags it as Maybank
            final_company_id = article_data.company_id
            
            try:
                # Need to import locally to avoid circular imports if any (though routers usually fine)
                from app.services.company_service import company_service
                
                # Check for companies in title
                found_companies = company_service.find_companies_by_text(article_data.title, session)
                
                if found_companies:
                    # Logic: If we found companies, and the current assigned company is NOT the "Subject"
                    # We prioritize the subject. 
                    
                    # Heuristic: If multiple found, pick the first one that IS NOT the source/provider
                    chosen_company = found_companies[0] # Default to first found
                    
                    # If we have multiple, try to be smarter? 
                    # For "Bermaz Auto gains Buy call from from Maybank", both Bermaz and Maybank might be found.
                    # We want Bermaz.
                    
                    # If the current assigned ID (e.g. Maybank) is in the found list, but there are OTHERS,
                    # likely the others are the subject.
                    
                    current_assigned_match = next((c for c in found_companies if str(c.id) == article_data.company_id), None)
                    
                    if current_assigned_match and len(found_companies) > 1:
                        # The assigned one is mentioned, but so are others. 
                        # Pick the one that IS NOT the assigned one (assuming assigned one is the 'source' of the search)
                        others = [c for c in found_companies if str(c.id) != article_data.company_id]
                        if others:
                            chosen_company = others[0]
                            print(f"Smart Ingestion: Re-tagging '{article_data.title}' from {current_assigned_match.name} -> {chosen_company.name}")
                            final_company_id = chosen_company.id
                            
                    elif not current_assigned_match and found_companies:
                        # The assigned one is NOT found in title (loop context was loose), but we found a specific one.
                        # Always take specific one.
                        print(f"Smart Ingestion: Re-tagging '{article_data.title}' from ID {article_data.company_id} -> {chosen_company.name}")
                        final_company_id = chosen_company.id
                        
            except Exception as e:
                print(f"Smart Ingestion Error: {e}")

            # SECONDARY DUPLICATE CHECK: URL + Company
            # Native ID might change or be unstable from frontend. URL is usually stable.
            existing_url = session.exec(select(NewsArticle).where(
                NewsArticle.url == article_data.url,
                NewsArticle.company_id == final_company_id
            )).first()
            
            if existing_url:
                print(f"[STORE] Skipped duplicate article by URL: {article_data.title[:50]}...")
                continue

            # Create and save article
            article = NewsArticle(
                company_id=final_company_id,
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
        
        # Get the newly saved articles for task queuing
        newly_saved = session.exec(
            select(NewsArticle).where(
                NewsArticle.native_id.in_([a.native_id for a in articles])
            )
        ).all()
        
        # Queue tasks for newly saved articles
        for article in newly_saved:
            if article.source.lower() == "bursa":
                # Skip Bursa articles for both sentiment and enrichment
                continue
            
            content_length = len(article.content) if article.content else 0
            
            if content_length < 500:
                # Short content: Queue enrichment first, which will trigger sentiment after
                from app.tasks.article_enrichment_tasks import enrich_article_content_task
                enrich_article_content_task.delay(str(article.id))
                print(f"[STORE] Queued content enrichment for article {article.id} ({content_length} chars)")
            else:
                # Substantial content: Queue sentiment analysis directly
                if not article.analyzed_at:
                    analyze_article_sentiment_task.delay(str(article.id))
                    print(f"[STORE] Queued sentiment analysis for article {article.id}")
    
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


@router.post("/enrich-content")
def trigger_content_enrichment(
    limit: int = 50,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    """
    Manually trigger content enrichment for articles with short/missing content.
    Uses newspaper3k to fetch full article text from URLs.
    """
    from app.tasks.article_enrichment_tasks import enrich_all_articles_task
    
    # Queue the task
    task = enrich_all_articles_task.delay(limit=limit)
    
    return {
        "message": f"Content enrichment queued for up to {limit} articles",
        "task_id": task.id
    }