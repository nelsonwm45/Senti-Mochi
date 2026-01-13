"""
Sentiment Analysis Tasks
Background tasks for analyzing news article sentiment
"""
from app.celery_app import celery_app
from app.services.sentiment import sentiment_analyzer
from sqlmodel import Session
from app.database import engine
from app.models import NewsArticle, Company
from sqlmodel import select


@celery_app.task(name="analyze_article_sentiment_task")
def analyze_article_sentiment_task(article_id: str):
    """
    Celery task to analyze sentiment of a single article.
    Called asynchronously when a new article is stored.
    """
    try:
        with Session(engine) as session:
            # Fetch the article and its company
            article = session.get(NewsArticle, article_id)
            if not article:
                print(f"Article {article_id} not found")
                return False
            
            company = session.get(Company, article.company_id)
            if not company:
                print(f"Company for article {article_id} not found")
                return False
            
            # Analyze and store
            result = sentiment_analyzer.analyze_and_store(article, company, session)
            
            if result:
                print(f"Successfully analyzed sentiment for article {article_id}")
            
            return result
    except Exception as e:
        print(f"Error in analyze_article_sentiment_task: {e}")
        return False


@celery_app.task(name="analyze_all_unanalyzed_articles_task")
def analyze_all_unanalyzed_articles_task(limit: int = 50):
    """
    Celery task to analyze all unanalyzed news articles.
    Can be run periodically to catch up on sentiment analysis.
    Skips Bursa announcements and articles without content.
    """
    print(f"Starting sentiment analysis for up to {limit} unanalyzed articles...")
    
    try:
        with Session(engine) as session:
            count = sentiment_analyzer.analyze_unanalyzed_articles(session, limit=limit)
            print(f"Sentiment analysis completed. Analyzed {count} articles.")
            return count
    except Exception as e:
        print(f"Error in analyze_all_unanalyzed_articles_task: {e}")
        return 0
