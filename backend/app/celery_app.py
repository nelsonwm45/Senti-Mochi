from celery import Celery
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "finance_api",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Import tasks to register them
# Import tasks to register them
from app.tasks import document_tasks  # noqa
from app.tasks import company_tasks  # noqa
from app.tasks import data_tasks  # noqa
from app.tasks import sentiment_tasks  # noqa

celery_app.conf.beat_schedule = {
    "seed-companies-every-24h": {
        "task": "seed_companies_task",
        "schedule": 86400.0,  # 24 hours
    },
    "update-all-news-every-1h": {
        "task": "update_all_news_task",
        "schedule": 3600.0,  # 1 hour
    },
    "update-all-financials-every-24h": {
        "task": "update_all_financials_task",
        "schedule": 86400.0,  # 24 hours
    },
}
