
from sqlmodel import Session, select
from app.database import engine
from app.models import AnalysisReport, Company
import sys

def delete_all_for_company():
    with Session(engine) as session:
        # Get Maybank
        company = session.exec(select(Company).where(Company.ticker == "1155.KL")).first()
        if not company:
            print("Company not found")
            return

        # Get all reports
        stmt = select(AnalysisReport).where(AnalysisReport.company_id == company.id)
        reports = session.exec(stmt).all()
        
        if reports:
            print(f"Found {len(reports)} reports. Deleting all...")
            for r in reports:
                session.delete(r)
            session.commit()
            print("All deleted.")
        else:
            print("No reports found.")

if __name__ == "__main__":
    delete_all_for_company()
