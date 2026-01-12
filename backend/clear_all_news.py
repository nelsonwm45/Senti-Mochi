from sqlmodel import Session, delete
from app.database import engine
from app.models import NewsArticle, SentimentAnalysis

def clear_all_news():
    with Session(engine) as session:
        print("Clearing ALL news data...")
        session.exec(delete(SentimentAnalysis))
        session.exec(delete(NewsArticle))
        session.commit()
        print("All news deleted.")

if __name__ == "__main__":
    clear_all_news()
