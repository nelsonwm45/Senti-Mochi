
from sqlmodel import Session, select
from app.database import engine
from app.models import Company, AnalysisReport

with Session(engine) as session:
    # 1. Find Company ID for 1155.KL
    statement = select(Company).where(Company.ticker == "1155.KL")
    company = session.exec(statement).first()
    
    if not company:
        print("Company 1155.KL not found in DB.")
    else:
        print(f"Company Found: {company.name} (ID: {company.id})")
        
        # 2. Find Reports
        repo_stmt = select(AnalysisReport).where(AnalysisReport.company_id == company.id)
        reports = session.exec(repo_stmt).all()
        
        print(f"Found {len(reports)} reports.")
        for r in reports:
            print(f"Report ID: {r.id}")
            print(f"Created At: {r.created_at}")
            print(f"Confidence: {r.confidence_score}")
            print(f"Rating: {r.rating}")
