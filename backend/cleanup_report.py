
from sqlmodel import Session, select
from app.database import engine
from app.models import AnalysisReport

report_id = "04da7a50-4946-484b-bdfd-a88cd0bb2196"

with Session(engine) as session:
    report = session.get(AnalysisReport, report_id)
    if report:
        session.delete(report)
        session.commit()
        print(f"Deleted stale report {report_id}")
    else:
        print("Report not found.")
