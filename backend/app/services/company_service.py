import yfinance as yf
from typing import Optional
from sqlmodel import Session, select, func
from app.models import Company
from app.database import engine

# Common names mapping - ticker to layman's name for better news searching
COMMON_NAMES = {
    '1155.KL': 'Maybank',           # Malayan Banking Berhad
    '1295.KL': 'Public Bank',       # Public Bank Bhd
    '1023.KL': 'CIMB',              # CIMB Group Holdings Berhad
    '1015.KL': 'AmBank',            # AMMB Holdings
    '5819.KL': 'Hong Leong Bank',   # Hong Leong Bank Bhd
    '1066.KL': 'RHB Bank',          # RHB Bank Bhd
    '2488.KL': 'Alliance Bank',     # Alliance Bank Malaysia
    '5185.KL': 'Affin Bank',        # Affin Bank Berhad
    '5258.KL': 'Bank Islam',        # Bank Islam Malaysia Berhad
    '5347.KL': 'Tenaga',            # Tenaga Nasional Berhad
    '5183.KL': 'PetChem',           # Petronas Chemicals Group
    '5225.KL': 'IHH',               # IHH Healthcare Berhad
    '6947.KL': 'Celcom',            # Celcom Axiata
    '8869.KL': 'Press Metal',       # Press Metal Aluminium
    '1961.KL': 'IOI',               # IOI Corporation Berhad
    '4197.KL': 'Sime Darby',        # Sime Darby Bhd
    '6012.KL': 'Maxis',             # Maxis Berhad
    '3182.KL': 'Genting',           # Genting Bhd
    '4715.KL': 'Genting Malaysia',  # Genting Malaysia Berhad
    '7277.KL': 'Dialog',            # Dialog Group Berhad
    '5398.KL': 'Gamuda',            # Gamuda Berhad
    '4707.KL': 'Nestle',            # Nestle Malaysia Berhad
    '2445.KL': 'KL Kepong',         # Kuala Lumpur Kepong Berhad
    '4065.KL': 'PPB',               # Perlis Plantations Berhad
    '6033.KL': 'Petronas Gas',      # Petronas Gas Berhad
    '5014.KL': 'Petronas Dagangan', # Petronas Dagangan Berhad
    '4863.KL': 'TM',                # Telekom Malaysia Berhad
    '7084.KL': 'QL Resources',      # QL Resources Berhad
    '5296.KL': 'Mr DIY',            # Mr DIY Group Berhad
    '4677.KL': 'YTL',               # YTL Corporation Berhad
    '6742.KL': 'YTL Power',         # YTL Power International Berhad
    '0156.KL': 'Top Glove',         # Top Glove Corporation Bhd
    '7113.KL': 'Hartalega',         # Hartalega Holdings Berhad
    '5284.KL': 'Kossan',            # Kossan Rubber Industries Berhad
    '0034.KL': 'Supermax',          # Supermax Corporation Berhad
    '5168.KL': 'Axiata',            # Axiata Group Berhad
    '5052.KL': 'BAT',               # British American Tobacco
    '3034.KL': 'F&N',               # Fraser & Neave Holdings Berhad
    '5602.KL': 'Padini',            # Padini Holdings Berhad
    '5248.KL': 'Bermaz',            # Bermaz Auto Berhad
    '1818.KL': 'Bursa',             # Bursa Malaysia
    '0085.KL': 'Mlabs',             # Mlabs Systems Berhad
}

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
    '0085.KL',  # Mlabs Systems Berhad
    
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
        Fetches details from yfinance and adds common names for news searching.
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
                        # Update common_name if not already set
                        if not existing.common_name and ticker in COMMON_NAMES:
                            existing.common_name = COMMON_NAMES[ticker]
                            session.add(existing)
                            session.commit()
                        continue
                    
                    print(f"Fetching {ticker}...", end=" ", flush=True)
                    y_ticker = yf.Ticker(ticker)
                    info = y_ticker.info
                    
                    name = info.get('longName') or info.get('shortName') or ticker
                    sector = info.get('sector', 'Unknown')
                    sub_sector = info.get('industry', 'Unknown')
                    website = info.get('website')
                    common_name = COMMON_NAMES.get(ticker)
                    
                    company = Company(
                        name=name,
                        ticker=ticker,
                        common_name=common_name,
                        sector=sector,
                        sub_sector=sub_sector,
                        website_url=website
                    )
                    
                    session.add(company)
                    session.commit()
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
        Searches by common_name (layman's name), ticker, and full name.
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
            c_common = company.common_name.lower() if company.common_name else ""
            
            # 1. Exact Ticker (highest priority)
            if c_ticker in query_lower:
                score = 100
            
            # 2. Exact Common Name (e.g., "maybank", "cimb")
            elif c_common and c_common in query_lower:
                score = 95
                
            # 3. Ticker part (e.g., "1155" from "1155.KL")
            elif c_ticker.split('.')[0] in query_lower:
                score = 90
            
            # 4. Exact Full Name
            elif c_name in query_lower:
                score = 100
                
            # 5. First word of common name
            elif c_common and len(c_common.split()) > 0:
                first_word = c_common.split()[0]
                if len(first_word) > 2 and first_word in query_lower:
                    score = 85
                    
            # 6. First word of full name (fallback)
            else:
                first_word = c_name.split(' ')[0]
                ignored_words = {"bank", "group", "holdings", "berhad", "malaysia", "public"} 
                
                if len(first_word) > 2 and first_word not in ignored_words and first_word in query_lower:
                    score = 80
            
            # 7. Specific aliases (legacy support)
            if "maybank" in query_lower and "malayan banking" in c_name:
                score = max(score, 90)
            if "ambank" in query_lower and ("ammb" in c_name or "1015" in c_ticker):
                score = max(score, 90)
                
            if score >= 50:
                found_companies.append(company)
                seen_ids.add(company.id)
                
        return found_companies

company_service = CompanyService()
