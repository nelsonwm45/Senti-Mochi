from sqlmodel import Session, select
from app.database import engine
from app.models import NewsArticle

def check_data():
    with Session(engine) as session:
        articles = session.exec(select(NewsArticle).limit(5)).all()
        print(f"Found {len(articles)} articles.")
        for a in articles:
            print(f"\nTitle: {a.title}")
            print(f"URL: {a.url}")
            print(f"Content Length: {len(a.content) if a.content else 0}")
            print(f"Summary: {a.summary}")

if __name__ == "__main__":
    check_data()
