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
        news_service.sync_news(session)
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
    print("Automated financials update completed.")
