from sqlmodel import Session, select
from datetime import datetime, timedelta
import random

from app.database import engine
from app.models import NewsArticle, SentimentAnalysis, Company

def populate_data():
    with Session(engine) as session:
        print("Populating News Data...")
        
        # 1. Create or Get Company
        company = session.exec(select(Company).where(Company.ticker == "MAYBANK")).first()
        if not company:
            company = Company(
                name="Malayan Banking Berhad",
                ticker="MAYBANK",
                sector="Finance",
                market_cap=120000000000.0,
                summary="Maybank is the largest bank in Malaysia."
            )
            session.add(company)
            session.commit()
            session.refresh(company)
            print(f"Created Company: {company.name}")
        
        # 2. Add News Articles (Mocking what a scraper would find)
        articles = [
            {
                "title": "Maybank records robust Q3 earnings amid economic headwinds",
                "source": "The Edge",
                "url": "https://theedgemalaysia.com/mock-article-1",
                "published_at": datetime.now() - timedelta(hours=2),
                "sentiment": "Positive",
                "score": 0.85,
                "rationale": "Strong earnings growth reported."
            },
            {
                "title": "Bursa Malaysia closes lower on profit taking",
                "source": "The Star",
                "url": "https://thestar.com.my/mock-article-2",
                "published_at": datetime.now() - timedelta(hours=5),
                "sentiment": "Negative",
                "score": 0.4,
                "rationale": "Market closed lower."
            },
            {
                "title": "Tech sector outlook remains cautious for 2026",
                "source": "Bloomberg",
                "url": "https://bloomberg.com/mock-article-3",
                "published_at": datetime.now() - timedelta(hours=8),
                "sentiment": "Neutral",
                "score": 0.5,
                "rationale": "Cautious outlook."
            },
            {
                "title": "Govt announces new green energy incentives",
                "source": "Bernama",
                "url": "https://bernama.com/mock-article-4",
                "published_at": datetime.now() - timedelta(days=1),
                "sentiment": "Positive",
                "score": 0.9,
                "rationale": "Incentives are good for business."
            }
        ]
        
        for data in articles:
            # Check if exists
            existing = session.exec(select(NewsArticle).where(NewsArticle.title == data["title"])).first()
            if not existing:
                article = NewsArticle(
                    title=data["title"],
                    url=data["url"],
                    source_name=data["source"],
                    published_at=data["published_at"],
                    company_id=company.id if "Maybank" in data["title"] else None
                )
                session.add(article)
                session.commit()
                session.refresh(article)
                
                # Add Sentiment
                sentiment = SentimentAnalysis(
                    news_article_id=article.id,
                    score=data["sentiment"],
                    confidence_score=data["score"],
                    rationale=data["rationale"],
                    analyzed_at=datetime.now()
                )
                session.add(sentiment)
                session.commit()
                print(f"Added Article: {article.title}")
            else:
                print(f"Skipped existing: {data['title']}")

if __name__ == "__main__":
    populate_data()
