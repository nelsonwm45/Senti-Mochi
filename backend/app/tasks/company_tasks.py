from app.celery_app import celery_app
from app.services.company_service import company_service

@celery_app.task(name="seed_companies_task")
def seed_companies_task():
    """
    Celery task to seed companies.
    """
    print("Starting automated company seeding...")
    company_service.seed_companies()
    print("Automated company seeding completed.")
