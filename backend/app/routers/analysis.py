
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select, col
from app.database import get_session
from app.models import Company, AnalysisReport, AnalysisJob, AnalysisStatus
from app.agents.workflow import app_workflow
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter()

def update_job_status(
    session: Session,
    job_id: UUID,
    status: AnalysisStatus,
    current_step: Optional[str] = None,
    progress: Optional[int] = None,
    error_message: Optional[str] = None,
    report_id: Optional[UUID] = None
):
    """Helper to update job status within the workflow."""
    job = session.get(AnalysisJob, job_id)
    if job:
        job.status = status
        if current_step is not None:
            job.current_step = current_step
        if progress is not None:
            job.progress = progress
        if error_message is not None:
            job.error_message = error_message
        if report_id is not None:
            job.report_id = report_id
        if status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
            job.completed_at = datetime.now(timezone.utc)
        session.add(job)
        session.commit()

@router.post("/{company_id}", status_code=202)
def trigger_analysis(company_id: UUID, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    Triggers the Multi-Agent Investment Analysis for a company.
    Returns a job_id for status tracking.
    """
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Check for existing running analysis
    existing_job = session.exec(
        select(AnalysisJob)
        .where(AnalysisJob.company_id == company_id)
        .where(AnalysisJob.status.not_in([AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]))
    ).first()

    if existing_job:
        return {
            "message": "Analysis already in progress",
            "company_id": company_id,
            "job_id": existing_job.id,
            "status": existing_job.status
        }

    # Create new analysis job
    job = AnalysisJob(
        company_id=company_id,
        status=AnalysisStatus.PENDING,
        current_step="Initializing analysis",
        progress=0
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    def run_workflow():
        from app.database import engine
        from sqlmodel import Session as SyncSession

        print(f"Starting background work for {company.name} (Job: {job.id})")
        try:
            # Update status: Starting
            with SyncSession(engine) as db:
                update_job_status(db, job.id, AnalysisStatus.GATHERING_INTEL, "Gathering intelligence", 10)

            initial_state = {
                "company_id": str(company.id),
                "company_name": company.name,
                "job_id": str(job.id),  # Pass job_id for status updates
                "errors": []
            }
            result = app_workflow.invoke(initial_state)

            # Update status: Completed
            with SyncSession(engine) as db:
                # Find the latest report for this company
                latest_report = db.exec(
                    select(AnalysisReport)
                    .where(AnalysisReport.company_id == company_id)
                    .order_by(col(AnalysisReport.created_at).desc())
                ).first()

                update_job_status(
                    db, job.id,
                    AnalysisStatus.COMPLETED,
                    "Analysis complete",
                    100,
                    report_id=latest_report.id if latest_report else None
                )

            print(f"Workflow finished for {company.name}")
        except Exception as e:
            print(f"Workflow failed: {e}")
            with SyncSession(engine) as db:
                update_job_status(db, job.id, AnalysisStatus.FAILED, "Analysis failed", error_message=str(e))

    background_tasks.add_task(run_workflow)

    return {"message": "Analysis started", "company_id": company_id, "job_id": job.id}

@router.get("/{company_id}/status")
def get_analysis_status(company_id: UUID, session: Session = Depends(get_session)):
    """
    Get the status of the latest analysis job for a company.
    """
    job = session.exec(
        select(AnalysisJob)
        .where(AnalysisJob.company_id == company_id)
        .order_by(col(AnalysisJob.started_at).desc())
    ).first()

    if not job:
        return {
            "status": "no_analysis",
            "message": "No analysis has been run for this company"
        }

    return {
        "job_id": job.id,
        "status": job.status,
        "current_step": job.current_step,
        "progress": job.progress,
        "error_message": job.error_message,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "report_id": job.report_id
    }

@router.get("/job/{job_id}/status")
def get_job_status(job_id: UUID, session: Session = Depends(get_session)):
    """
    Get the status of a specific analysis job.
    """
    job = session.get(AnalysisJob, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "company_id": job.company_id,
        "status": job.status,
        "current_step": job.current_step,
        "progress": job.progress,
        "error_message": job.error_message,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "report_id": job.report_id
    }

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

@router.delete("/report/{report_id}")
def delete_report(report_id: UUID, session: Session = Depends(get_session)):
    """
    Deletes a specific analysis report.
    """
    report = session.get(AnalysisReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    session.delete(report)
    session.commit()
    return {"message": "Report deleted successfully", "report_id": str(report_id)}
