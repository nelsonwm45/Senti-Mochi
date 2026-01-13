import sys
import os
from sqlmodel import Session, select
# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import engine
from app.models import Company, NewsArticle
from app.services.company_service import company_service

def check_and_fix():
    with Session(engine) as session:
        # Find Bermaz
        bermaz = session.exec(select(Company).where(Company.ticker == "5248.KL")).first()
        if not bermaz:
            print("Bermaz not found in DB!")
            return

        print(f"Bermaz ID: {bermaz.id}")
        
        # Check news for Bermaz
        news = session.exec(select(NewsArticle).where(NewsArticle.company_id == bermaz.id)).all()
        print(f"Current Bermaz News Count: {len(news)}")
        for n in news:
            print(f"- {n.title} (Source: {n.source})")
            
        # Check for the specific article (likely tagged as Maybank)
        # We'll search by title text patterns
        query = "Bermaz Auto gains 'Buy' call from Maybank IB"
        candidates = session.exec(select(NewsArticle).where(NewsArticle.title.contains("Bermaz Auto"))).all()
        
        print("\nChecking candidates with 'Bermaz Auto' in title:")
        for c in candidates:
            print(f"- Title: {c.title}")
            print(f"  Current Tag ID: {c.company_id}")
            if c.company_id != bermaz.id:
                print(f"  [MISMATCH] Should be Bermaz ({bermaz.id})")
                # Fix it
                c.company_id = bermaz.id
                session.add(c)
                print(f"  -> FIXED tag to Bermaz")
        
        session.commit()
        print("\nFix complete.")

if __name__ == "__main__":
    check_and_fix()
