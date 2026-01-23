
from sqlmodel import Session, select
from app.database import engine
from app.models import AnalysisReport, Company
import sys

def delete_latest():
    with Session(engine) as session:
        # Get Maybank
        company = session.exec(select(Company).where(Company.ticker == "1155.KL")).first()
        if not company:
            print("Company not found")
            return

        # Get latest report
        stmt = select(AnalysisReport).where(AnalysisReport.company_id == company.id).order_by(AnalysisReport.created_at.desc())
        report = session.exec(stmt).first()
        
        if report:
            print(f"Deleting report {report.id} created at {report.created_at}")
            session.delete(report)
            session.commit()
            print("Deleted.")
        else:
            print("No reports found.")

if __name__ == "__main__":
    delete_latest()
