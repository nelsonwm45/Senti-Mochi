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
from app.tasks.vector_tasks import vectorize_article_task

# Schema for storing articles from client
class ClientNewsArticle(BaseModel):
    company_id: str
    source: str
    native_id: str
    title: str
    url: str
    published_at: str  # ISO string from frontend
    content: Optional[str] = None

# Internal helper function for storing articles (used by both API and workflow)
def store_articles_internal(articles_data: List[dict], session: Session, company_id: Optional[str] = None) -> dict:
    """
    Internal helper to store news articles from various sources.
    Handles duplicate detection, content fetching, and queuing vectorization/sentiment tasks.
    Can be called from API endpoints or background workflows.
    
    Args:
        articles_data: List of article dicts with keys: source, native_id, title, url, published_at, content, company_id (optional)
        session: Database session
        company_id: Optional company UUID to tag articles with (overrides articles_data.company_id)
    
    Returns:
        Dict with keys: saved (int), skipped (int), total (int)
    """
    from app.services.article_fetcher import article_fetcher_service
    from app.services.company_service import company_service
    
    saved_count = 0
    skipped_count = 0
    
    for article_data in articles_data:
        try:
            # Determine company to tag with
            final_company_id = company_id or article_data.get('company_id')
            
            # Check if article already exists (by native_id OR exact title match)
            existing = session.exec(select(NewsArticle).where(
                (NewsArticle.native_id == article_data['native_id']) | 
                (NewsArticle.title == article_data['title'])
            )).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # Parse datetime
            try:
                published_at = datetime.fromisoformat(article_data['published_at'].replace('Z', '+00:00'))
            except:
                published_at = datetime.utcnow()
            
            # Smart company re-tagging: Check if article title mentions other companies
            if final_company_id:
                try:
                    found_companies = company_service.find_companies_by_text(article_data['title'], session)
                    if found_companies:
                        current_assigned_match = next((c for c in found_companies if str(c.id) == str(final_company_id)), None)
                        
                        if current_assigned_match and len(found_companies) > 1:
                            # Assigned company found, but others too - pick the others
                            others = [c for c in found_companies if str(c.id) != str(final_company_id)]
                            if others:
                                final_company_id = others[0].id
                                print(f"[STORE] Smart re-tagging '{article_data['title'][:50]}' to {others[0].name}")
                        elif not current_assigned_match and found_companies:
                            # Assigned company NOT found, use found one
                            final_company_id = found_companies[0].id
                            print(f"[STORE] Smart tagging '{article_data['title'][:50]}' to {found_companies[0].name}")
                except Exception as e:
                    print(f"[STORE] Smart tagging error: {e}")
            
            # Fetch full article content (skip Bursa)
            full_content = article_data.get('content') or article_data['title']
            if article_data['source'].lower() != 'bursa' and article_data.get('url'):
                print(f"[STORE] Fetching full content for {article_data['title'][:50]}...")
                fetched_content = article_fetcher_service.fetch_article_content(article_data['url'])
                if fetched_content:
                    full_content = fetched_content
                    print(f"[STORE] Fetched {len(full_content)} chars")
            
            # Create and save article
            article = NewsArticle(
                company_id=final_company_id,
                source=article_data['source'],
                native_id=article_data['native_id'],
                title=article_data['title'],
                url=article_data.get('url', ''),
                published_at=published_at,
                content=full_content
            )
            session.add(article)
            saved_count += 1
            
        except Exception as e:
            if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                print(f"[STORE] Skipping duplicate: {article_data.get('native_id')}")
                skipped_count += 1
            else:
                print(f"[STORE] Error storing article: {e}")
            continue
    
    if saved_count > 0:
        session.commit()
        
        # Queue sentiment analysis and vectorization for new articles
        native_ids = [a['native_id'] for a in articles_data]
        newly_saved = session.exec(
            select(NewsArticle).where(NewsArticle.native_id.in_(native_ids))
        ).all()
        
        for article in newly_saved:
            if article.source.lower() != "bursa" and not article.analyzed_at:
                analyze_article_sentiment_task.delay(str(article.id))
                print(f"[STORE] Queued sentiment analysis for {article.id}")
            
            vectorize_article_task.delay(str(article.id))
            print(f"[STORE] Queued vectorization for {article.id}")
    
    return {
        "saved": saved_count,
        "skipped": skipped_count,
        "total": len(articles_data)
    }

@router.post("/store-articles")
def store_articles(
    articles: List[ClientNewsArticle],
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    """
    Store news articles fetched from client-side APIs.
    Used for Bursa Malaysia and other APIs that can only be called from the browser.
    Fetches full article content immediately before storing.
    """
    # Convert Pydantic models to dicts and use internal helper
    articles_data = [
        {
            'company_id': str(article.company_id),
            'source': article.source,
            'native_id': article.native_id,
            'title': article.title,
            'url': article.url,
            'published_at': article.published_at,
            'content': article.content
        }
        for article in articles
    ]
    
    return store_articles_internal(articles_data, session)

@router.post("/search")
def search_news(
    keyword: str = Query(..., description="Search keyword (e.g., 'Maybank', 'Top Glove ESG')"),
    sources: Optional[List[str]] = Query(None, description="News sources to search (star, nst, edge). Defaults to all."),
    company_id: Optional[str] = Query(None, description="Optional company ID to tag articles with"),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    """
    Search for news articles by keyword from backend.
    
    Fetches news from Star, NST, and The Edge, stores them, and returns the articles.
    This endpoint allows frontend to search for specific keywords without doing the fetching itself.
    
    Example:
    - /search?keyword=Maybank
    - /search?keyword=Top%20Glove%20ESG&sources=star&sources=nst&sources=edge
    - /search?keyword=Ambank&company_id=<company_uuid>
    - /search?keyword=ESG&sources=edge (search only The Edge)
    """
    from app.services.news_fetcher import news_fetcher_service
    from app.services.article_fetcher import article_fetcher_service
    
    # Default to all sources if not specified
    if sources is None:
        sources = ['star', 'nst', 'edge']
    
    print(f"[SEARCH_NEWS] Searching for '{keyword}' in sources: {sources}")
    
    # Fetch articles from specified sources
    fetch_result = news_fetcher_service.fetch_news_by_keyword(keyword, sources)
    
    print(f"[SEARCH_NEWS] Fetch result - Total: {fetch_result.get('total')}")
    for source in sources:
        count = len(fetch_result.get(source, []))
        print(f"[SEARCH_NEWS]   {source}: {count} articles")
    
    # Collect all articles to store
    articles_to_store = []
    
    # Process articles from each source
    for source in sources:
        if source in fetch_result:
            source_articles = fetch_result[source]
            print(f"[SEARCH_NEWS] Processing {len(source_articles)} {source} articles")
            for article_data in source_articles:
                # Determine which company to tag with
                final_company_id = company_id
                
                # If no company_id specified, try to find matching companies in the article title
                if not final_company_id:
                    try:
                        from app.services.company_service import company_service
                        found_companies = company_service.find_companies_by_text(article_data['title'], session)
                        if found_companies:
                            final_company_id = found_companies[0].id
                            print(f"[SEARCH_NEWS] Auto-tagged '{article_data['title'][:50]}' to {found_companies[0].name}")
                    except Exception as e:
                        print(f"[SEARCH_NEWS] Auto-tagging error: {e}")
                
                # Only add if we have a company to tag with
                if final_company_id:
                    articles_to_store.append({
                        'company_id': str(final_company_id),
                        'source': article_data['source'],
                        'native_id': article_data['native_id'],
                        'title': article_data['title'],
                        'url': article_data['url'],
                        'published_at': article_data['published_at'],
                        'content': article_data['content']
                    })
                else:
                    print(f"[SEARCH_NEWS] Skipping article (no company): {article_data['title'][:50]}")
    
    print(f"[SEARCH_NEWS] Collected {len(articles_to_store)} articles to store out of {fetch_result.get('total', 0)} fetched")
    
    # Store articles using the existing store logic
    stored_articles = []
    if articles_to_store:
        # Convert to ClientNewsArticle objects and store
        from app.routers.news import ClientNewsArticle
        client_articles = [ClientNewsArticle(**article) for article in articles_to_store]
        
        saved_count = 0
        skipped_count = 0
        
        for article_data in client_articles:
            try:
                # Check if article already exists
                existing = session.exec(select(NewsArticle).where(
                    (NewsArticle.native_id == article_data.native_id) | 
                    (NewsArticle.title == article_data.title)
                )).first()
                
                if existing:
                    skipped_count += 1
                    stored_articles.append({
                        'id': str(existing.id),
                        'title': existing.title,
                        'url': existing.url,
                        'source': existing.source,
                        'published_at': existing.published_at.isoformat(),
                        'company_id': str(existing.company_id),
                        'status': 'existing'
                    })
                    continue
                
                # Parse datetime
                try:
                    published_at = datetime.fromisoformat(article_data.published_at.replace('Z', '+00:00'))
                except:
                    published_at = datetime.utcnow()
                
                # Fetch full content
                full_content = article_data.content or article_data.title
                if article_data.source.lower() != 'bursa' and article_data.url:
                    print(f"[SEARCH_NEWS] Fetching full content for {article_data.title[:50]}...")
                    fetched_content = article_fetcher_service.fetch_article_content(article_data.url)
                    if fetched_content:
                        full_content = fetched_content
                
                # Create and save article
                article = NewsArticle(
                    company_id=article_data.company_id,
                    source=article_data.source,
                    native_id=article_data.native_id,
                    title=article_data.title,
                    url=article_data.url,
                    published_at=published_at,
                    content=full_content
                )
                session.add(article)
                saved_count += 1
                
                stored_articles.append({
                    'id': str(article.id),
                    'title': article.title,
                    'url': article.url,
                    'source': article.source,
                    'published_at': article.published_at.isoformat(),
                    'company_id': str(article.company_id),
                    'status': 'new'
                })
                
            except Exception as e:
                print(f"[SEARCH_NEWS] Error storing article: {e}")
                continue
        
        if saved_count > 0:
            session.commit()
            
            # Queue sentiment analysis for newly saved articles
            for article_dict in stored_articles:
                if article_dict['status'] == 'new' and article_dict['source'].lower() != 'bursa':
                    # Get the article from DB and queue sentiment analysis
                    article = session.get(NewsArticle, article_dict['id'])
                    if article and not article.analyzed_at:
                        analyze_article_sentiment_task.delay(str(article.id))
                        print(f"[SEARCH_NEWS] Queued sentiment analysis for article {article.id}")
    
    return {
        'keyword': keyword,
        'sources': sources,
        'total_fetched': fetch_result.get('total', 0),
        'total_stored': len(stored_articles),
        'articles': stored_articles
    }


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