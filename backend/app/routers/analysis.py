
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select, col
from app.database import get_session
from app.models import Company, AnalysisReport, AnalysisJob, AnalysisStatus, User
from app.auth import get_current_user
from app.agents.workflow import app_workflow
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone
from app.routers.news import store_articles_internal

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
def trigger_analysis(
    company_id: UUID,
    topic: Optional[str] = None,
    company_name: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers the Multi-Agent Investment Analysis for a company.
    Uses the user's analysis_persona to determine analysis focus.
    Can fetch fresh news based on topic (esg, financials, general).
    Returns a job_id for status tracking.
    """
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get user's analysis persona (default to INVESTOR)
    analysis_persona = getattr(current_user, 'analysis_persona', 'INVESTOR')
    if hasattr(analysis_persona, 'value'):
        analysis_persona = analysis_persona.value  # Convert enum to string

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
            "status": existing_job.status,
            "analysis_persona": existing_job.analysis_persona
        }

    # Create new analysis job with persona
    job = AnalysisJob(
        company_id=company_id,
        analysis_persona=analysis_persona,
        status=AnalysisStatus.PENDING,
        current_step="Initializing analysis",
        progress=0
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    # Capture persona and topic for background task
    job_persona = analysis_persona
    job_topic = topic
    job_company_name = company_name or company.name

    def run_workflow():
        from app.database import engine
        from sqlmodel import Session as SyncSession
        from app.services.news_fetcher import news_fetcher_service
        from app.services.article_fetcher import article_fetcher_service

        print(f"Starting background work for {company.name} (Job: {job.id}) [Persona: {job_persona}]")
        try:
            # Fetch news based on topic if provided
            if job_topic:
                print(f"[WORKFLOW] Fetching news for topic: {job_topic}")
                
                # Build keyword based on topic
                if job_topic.lower() == 'esg':
                    search_keyword = f"{job_company_name} ESG"
                elif job_topic.lower() == 'financials':
                    search_keyword = f"{job_company_name} Financial"
                else:  # general
                    search_keyword = job_company_name
                
                print(f"[WORKFLOW] News search keyword: {search_keyword}")
                
                # Fetch news from all sources
                news_results = news_fetcher_service.fetch_news_by_keyword(
                    search_keyword, 
                    sources=['star', 'nst', 'edge']
                )
                
                print(f"[WORKFLOW] Fetched {news_results.get('total', 0)} articles from news sources")
                
                # Store articles if found
                if news_results.get('total', 0) > 0:
                    articles_to_store = []
                    
                    # Collect articles from all sources
                    for source in ['star', 'nst', 'edge']:
                        if source in news_results:
                            articles_to_store.extend(news_results[source])
                    
                    # Store articles and queue vectorization/sentiment tasks
                    with SyncSession(engine) as db:
                        store_articles_internal(articles_to_store, db, company_id)
            
            # Update status: Starting workflow
            with SyncSession(engine) as db:
                update_job_status(db, job.id, AnalysisStatus.GATHERING_INTEL, "Gathering intelligence", 10)

            initial_state = {
                "company_id": str(company.id),
                "company_name": company.name,
                "job_id": str(job.id),  # Pass job_id for status updates
                "analysis_persona": job_persona,  # Pass persona for polymorphic analysis
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

    return {
        "message": "Analysis started",
        "company_id": company_id,
        "job_id": job.id,
        "analysis_persona": job_persona
    }

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
