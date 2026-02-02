from app.celery_app import celery_app
from app.services.news_service import news_service
from app.services.finance import finance_service
from app.services.company_service import company_service
from sqlmodel import Session, select
from app.database import engine
from app.models import Company

@celery_app.task(name="update_all_news_task")
def update_all_news_task():
    """
    Celery task to update news for all seeded companies.
    """
    print("Starting automated news update...")
    with Session(engine) as session:
        # Only update companies that are seeded (have tickers)
        # Maybe limit to active watchlist companies? For now update all seeded ones.
        # But wait, seed_companies.py adds them. 
        # Let's iterate all companies.
        news_service.sync_news(session=session)
    print("Automated news update completed.")

@celery_app.task(name="update_all_financials_task")
def update_all_financials_task():
    """
    Celery task to update financials for all seeded companies.
    """
    print("Starting automated financials update...")
    with Session(engine) as session:
        companies = session.exec(select(Company)).all()
        for company in companies:
            if company.ticker:
                finance_service.sync_financials(company.ticker, session)
    print(f"Automated financial data update completed.")

@celery_app.task(name="update_company_news_task")
def update_company_news_task(ticker: str):
    """
    Fetch and store news for a single company.
    Called when user adds a company to their watchlist for immediate news.
    """
    print(f"[NEWS] Fetching news for {ticker}...")
    
    with Session(engine) as session:
        # Find the company
        company = session.exec(
            select(Company).where(Company.ticker == ticker)
        ).first()
        
        if not company:
            print(f"[NEWS] Company {ticker} not found in database")
            return
        
        # Sync news for this company
        try:
            count = news_service.sync_news(company.id, session)
            print(f"[NEWS] Fetched {count} articles for {company.name} ({ticker})")
        except Exception as e:
            print(f"[NEWS] Error fetching news for {ticker}: {e}")
    
    return None
