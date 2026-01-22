
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select, col
from app.database import get_session
from app.models import Company, AnalysisReport
from app.agents.workflow import app_workflow
from uuid import UUID
from typing import List

router = APIRouter()

@router.post("/{company_id}", status_code=202)
def trigger_analysis(company_id: UUID, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    Triggers the Multi-Agent Investment Analysis for a company.
    Runs in background.
    """
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    def run_workflow():
        print(f"Starting background work for {company.name}")
        try:
            initial_state = {
                "company_id": str(company.id), 
                "company_name": company.name,
                "errors": []
            }
            result = app_workflow.invoke(initial_state)
            print(f"Workflow finished for {company.name}")
        except Exception as e:
            print(f"Workflow failed: {e}")

    background_tasks.add_task(run_workflow)
    
    return {"message": "Analysis started", "company_id": company_id}

@router.get("/{company_id}/reports")
def get_reports(company_id: UUID, session: Session = Depends(get_session)):
    """
    Retrieves analysis reports for a company.
    """
    statement = (
        select(AnalysisReport)
        .where(AnalysisReport.company_id == company_id)
        .order_by(col(AnalysisReport.created_at).desc())
    )
    reports = session.exec(statement).all()
    return reports

@router.get("/report/{report_id}")
def get_report(report_id: UUID, session: Session = Depends(get_session)):
    """
    Retrieves a specific analysis report.
    """
    report = session.get(AnalysisReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
