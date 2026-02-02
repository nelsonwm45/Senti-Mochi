import requests
from datetime import datetime
from uuid import UUID
from sqlmodel import Session, select
from app.database import engine
from app.models import Company, NewsArticle
import urllib.parse
from app.services.company_service import company_service

class NewsService:
    @staticmethod
    def fetch_bursa_news(company: Company):
        """
        Disabled - Bursa news is now fetched from frontend to avoid CORS issues.
        """
        return []

    @staticmethod
    def fetch_star_news(company: Company):
        """
        Disabled - Star news is now fetched from frontend.
        """
        return []

    @staticmethod
    def fetch_nst_news(company: Company):
        """
        Disabled - NST news is now fetched from frontend.
        """
        return []

    @staticmethod
    def get_recent_articles(company_id: str, session: Session, limit: int = 5) -> list[NewsArticle]:
        """
        Retrieve recent news articles object list.
        """
        stmt = select(NewsArticle).where(NewsArticle.company_id == company_id).order_by(NewsArticle.published_at.desc()).limit(limit)
        return session.exec(stmt).all()

    @staticmethod
    def get_company_news_context(company_id: str, session: Session, limit: int = 5) -> str:
        """
        Retrieve recent news for a company formatted for LLM context.
        """
        articles = NewsService.get_recent_articles(company_id, session, limit)
        
        if not articles:
            return ""
            
        summary = "Recent News Headlines:\n"
        for article in articles:
            date_str = article.published_at.strftime("%Y-%m-%d")
            summary += f"- [{date_str}] {article.title} (Source: {article.source})\n"
            
            # Add content/summary if available
            if article.content:
                summary += f"  Summary: {article.content}\n"
            
        return summary + "\n"
    
    @staticmethod
    def sync_news(company_id: UUID = None, session: Session = None):
        """
        Main method to sync news for companies.
        If company_id is provided, sync only that company.
        Otherwise, sync all companies.
        """
        local_session = False
        if not session:
            session = Session(engine)
            local_session = True
            
        try:
            # Get companies to sync
            if company_id:
                # Sync single company
                company = session.get(Company, company_id)
                if not company:
                    print(f"Company ID {company_id} not found")
                    return 0
                companies = [company]
            else:
                # Sync all companies
                companies = session.exec(select(Company)).all()
            
            print(f"Syncing news for {len(companies)} companies...")
            
            total_saved = 0
            for company in companies:
                new_articles = []
                # Fetch from all sources
                new_articles.extend(NewsService.fetch_bursa_news(company))
                new_articles.extend(NewsService.fetch_star_news(company))
                new_articles.extend(NewsService.fetch_nst_news(company))
                
                count = 0
                for article in new_articles:
                    # Upsert check - rudimentary
                    existing = session.exec(select(NewsArticle).where(
                        NewsArticle.native_id == article.native_id
                    )).first()
                    
                    if not existing:
                        session.add(article)
                        count += 1
                
                if count > 0:
                    session.commit()
                    print(f"Saved {count} new articles for {company.name}")
                    total_saved += count
            
            return total_saved
                
        finally:
            if local_session:
                session.close()

news_service = NewsService()
