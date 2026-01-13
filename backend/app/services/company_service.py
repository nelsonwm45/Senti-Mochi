import yfinance as yf
from typing import Optional
from sqlmodel import Session, select, func
from app.models import Company
from app.database import engine

# Expanded list of major Bursa Malaysia companies (~70 companies)
# Includes FBMKLCI constituents, FBM100, and other major stocks
INITIAL_TICKERS = [
    # FBMKLCI Top 30
    '1155.KL',  # Maybank
    '1295.KL',  # Public Bank
    '1023.KL',  # CIMB
    '5347.KL',  # Tenaga Nasional
    '5183.KL',  # PetChem
    '5225.KL',  # IHH Healthcare
    '6947.KL',  # Celcomdigi
    '5819.KL',  # Hong Leong Bank
    '8869.KL',  # Press Metal
    '3816.KL',  # MISC
    '1961.KL',  # IOI Corp
    '4197.KL',  # Sime Darby
    '6012.KL',  # Maxis
    '1066.KL',  # RHB Bank
    '3182.KL',  # Genting
    '4715.KL',  # Genting Malaysia
    '1015.KL',  # AMMB Holdings (Ambank)
    '7277.KL',  # Dialog
    '5398.KL',  # Gamuda
    '4707.KL',  # Nestle Malaysia
    '2445.KL',  # KL Kepong
    '4065.KL',  # PPB Group
    '6033.KL',  # Petronas Gas
    '5014.KL',  # Petronas Dagangan
    '4863.KL',  # Telekom Malaysia
    '7084.KL',  # QL Resources
    '5296.KL',  # Mr DIY
    '4677.KL',  # YTL Corp
    '6742.KL',  # YTL Power
    '0166.KL',  # Inari Amertron
    
    # Additional Banks & Finance
    '2488.KL',  # Alliance Bank
    '5185.KL',  # Affin Bank
    '5258.KL',  # Bank Islam
    '1082.KL',  # Hong Leong Financial
    
    # Telecom & Technology
    '5168.KL',  # Axiata Group
    '0012.KL',  # MY E.G. Services
    '0097.KL',  # Globetronics
    '7036.KL',  # Unisem
    '0045.KL',  # Vitrox
    
    # Plantation
    '2216.KL',  # Sime Darby Plantation
    '5681.KL',  # Hap Seng Plantations
    '2291.KL',  # TSH Resources
    '5285.KL',  # IOI Properties
    
    # Property & Construction
    '1597.KL',  # Sunway Construction
    '2879.KL',  # UEM Sunrise
    '3069.KL',  # WCT Holdings
    '6475.KL',  # IJM Corp
    '3336.KL',  # Eco World Development
    
    # Consumer & Retail
    '5052.KL',  # British American Tobacco
    '3034.KL',  # Fraser & Neave
    '5602.KL',  # Padini Holdings
    
    # Healthcare & Gloves
    '0156.KL',  # Top Glove
    '7113.KL',  # Hartalega
    '5284.KL',  # Kossan Rubber
    '0034.KL',  # Supermax
    
    # Auto
    '5248.KL',  # Bermaz Auto
    
    # Industrial & Others
    '1818.KL',  # Bursa Malaysia
    '4898.KL',  # Batu Kawan
    '6399.KL',  # KLCCP Stapled Group
    '1503.KL',  # Cahya Mata Sarawak
    '5878.KL',  # Pavilion REIT
    '5020.KL',  # Petronas Chemicals Group
    '6888.KL',  # Axiata Group Bhd
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
    def find_companies_by_text(query: str, session: Session) -> list[Company]:
        """
        Find all companies mentioned in the text query.
        Returns a list of unique companies found.
        """
        query_lower = query.lower()
        companies = session.exec(select(Company)).all()
        
        found_companies = []
        seen_ids = set()
        
        for company in companies:
            if company.id in seen_ids:
                continue
                
            score = 0
            c_name = company.name.lower()
            c_ticker = company.ticker.lower()
            
            # 1. Exact Ticker
            if c_ticker in query_lower:
                score = 100
            
            # 2. Ticker part
            elif c_ticker.split('.')[0] in query_lower:
                score = 90
            
            # 3. Exact Name
            elif c_name in query_lower:
                score = 100
                
            # 4. First word (e.g. "CIMB", "Maybank")
            else:
                first_word = c_name.split(' ')[0]
                # Avoid matching generic words like "Bank", "Public" (unless "Public Bank" handled above), "Group"
                ignored_words = {"bank", "group", "holdings", "berhad", "malaysia", "public"} 
                
                if len(first_word) > 2 and first_word not in ignored_words and first_word in query_lower:
                     score = 80
            
            # 5. Aliases
            if "maybank" in query_lower and "malayan banking" in c_name:
                score = 90
            if "public bank" in query_lower and "public bank" in c_name:
                score = 90
            if "ambank" in query_lower and ("ammb" in c_name or "1015" in c_ticker):
                score = 90
                
            if score >= 50:
                found_companies.append(company)
                seen_ids.add(company.id)
                
        return found_companies

company_service = CompanyService()
