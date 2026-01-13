import yfinance as yf
from typing import Optional
from sqlmodel import Session, select, func
from app.models import Company
from app.database import engine

# Initial list of Bursa Malaysia tickers (from frontend/src/lib/bursaCompanies.ts + additions)
INITIAL_TICKERS = [
    '1155.KL', '1295.KL', '1023.KL', '5347.KL', '5183.KL',
    '5225.KL', '6947.KL', '5819.KL', '8869.KL', '3816.KL',
    '1961.KL', '4197.KL', '6012.KL', '1066.KL', '3182.KL',
    '4715.KL', '1015.KL', '7277.KL', '5398.KL', '4707.KL',
    '2445.KL', '4065.KL', '6033.KL', '5014.KL', '4863.KL',
    '7084.KL', '5296.KL', '4677.KL', '6742.KL', '0166.KL',
    '2488.KL', '5185.KL', '5258.KL', '1082.KL'
]

class CompanyService:
    @staticmethod
    def seed_companies(session: Session = None):
        """
        Seeds the database with initial companies if they don't exist.
        Fetches details from yfinance.
        """
        # If no session provided, create one
        local_session = False
        if not session:
            session = Session(engine)
            local_session = True

        try:
            print(f"Seeding {len(INITIAL_TICKERS)} companies...")
            for ticker in INITIAL_TICKERS:
                try:
                    # Check if exists
                    stmt = select(Company).where(Company.ticker == ticker)
                    existing = session.exec(stmt).first()
                    
                    if existing:
                        # Optional: Update existing if needed? For now, skip to save time/requests
                        continue
                    
                    print(f"Fetching {ticker}...", end=" ", flush=True)
                    y_ticker = yf.Ticker(ticker)
                    info = y_ticker.info
                    
                    name = info.get('longName') or info.get('shortName') or ticker
                    sector = info.get('sector', 'Unknown')
                    sub_sector = info.get('industry', 'Unknown')
                    website = info.get('website')
                    
                    company = Company(
                        name=name,
                        ticker=ticker,
                        sector=sector,
                        sub_sector=sub_sector,
                        website_url=website
                    )
                    
                    session.add(company)
                    session.commit() # Commit each to avoid rollback on single failure? Or bulk?
                    # Let's commit each for robustness in this script
                    print(f"Done! ({name})")
                    
                except Exception as e:
                    print(f"Failed to fetch/add {ticker}: {e}")
            
        finally:
            if local_session:
                session.close()

    @staticmethod
    def get_company_count(session: Session) -> int:
        statement = select(func.count(Company.id))
        return session.exec(statement).one()

    @staticmethod
    def find_company_by_text(query: str, session: Session) -> Optional[Company]:
        """
        Find a company based on text query (ticker or name).
        """
        clean_q = query.strip()
        
        # 1. Try exact ticker match
        stmt = select(Company).where(Company.ticker == clean_q.upper())
        company = session.exec(stmt).first()
        if company:
            return company
            
        # 2. Try name case-insensitive match
        # Simple heuristic: if query is short, might be part of name
        # If query is long, use RAG.
        # But for "Analyse CIMB", "CIMB" is the keyword.
        # We'll rely on the caller to extract the entity or just pass the whole query?
        # Passing whole query "Analyse CIMB bank" to ilike %Analyse CIMB bank% won't work.
        # The extraction log belongs in RAG service. 
        # BUT, for simplicity, we can try to match if the query *contains* the company name? 
        # No, that's expensive (listing all companies).
        
        # Better: Search *for* the query tokens?
        # Let's support simple substring search for now.
        stmt = select(Company).where(Company.name.ilike(f"%{clean_q}%"))
        company = session.exec(stmt).first()
        if company: 
            return company

        return None

company_service = CompanyService()
