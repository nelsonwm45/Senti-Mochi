from sqlmodel import Session, select, delete
from app.database import engine
from app.models import NewsArticle, SentimentAnalysis

def clean_data():
    with Session(engine) as session:
        print("Cleaning mock data...")
        
        # 1. Select mock articles (identified by 'mock' in URL or specific titles)
        statement = select(NewsArticle).where(
            (NewsArticle.url.contains("mock")) | 
            (NewsArticle.source_name == "The Edge") | # The previous mock scraper used this source name exclusively with fake data usually
            (NewsArticle.url.contains("example.com"))
        )
        articles = session.exec(statement).all()
        
        for article in articles:
            # Delete associated sentiment analysis first (if cascading not set)
            session.exec(delete(SentimentAnalysis).where(SentimentAnalysis.news_article_id == article.id))
            
            # Delete article
            session.delete(article)
            print(f"Deleted Mock Article: {article.title}")
            
        session.commit()
        print("Cleanup complete.")

if __name__ == "__main__":
    clean_data()
