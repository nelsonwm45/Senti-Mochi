
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
                
                # Build search keyword based on topic
                # Note: fetch_news_by_company will use company.common_name (e.g., "Maybank")
                # and append topic suffix for more targeted searches
                if job_topic.lower() == 'esg':
                    # Fetch by company with ESG topic suffix
                    news_results = news_fetcher_service.fetch_news_by_keyword(
                        f"{company.common_name or company.name} ESG",
                        sources=['star', 'nst', 'edge']
                    )
                elif job_topic.lower() == 'financials':
                    # Fetch by company with financials topic suffix
                    news_results = news_fetcher_service.fetch_news_by_keyword(
                        f"{company.common_name or company.name} Financial",
                        sources=['star', 'nst', 'edge']
                    )
                else:  # general
                    # Fetch by company using common_name for better matching
                    news_results = news_fetcher_service.fetch_news_by_company(
                        company,
                        sources=['star', 'nst', 'edge']
                    )
                
                print(f"[WORKFLOW] Fetched news using keyword: {company.common_name or company.name}")
                
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

@router.post("/report/{report_id}/talking-points/generate")
def generate_talking_points(
    report_id: UUID,
    session: Session = Depends(get_session)
):
    """
    Generates talking points for a Relationship Manager based on an existing analysis.
    """
    report = session.get(AnalysisReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    company = session.get(Company, report.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Import here to avoid circular dependencies if any
    from app.agents.base import get_llm
    from app.agents.prompts import TALKING_POINTS_SYSTEM, get_talking_points_prompt
    from langchain_core.messages import SystemMessage, HumanMessage
    import json

    # Construct the prompt
    # Construct the prompt with safe defaults
    try:
        financial_json = json.dumps(report.financial_analysis) if report.financial_analysis else "{}"
        claims_json = json.dumps(report.esg_analysis) if report.esg_analysis else "{}"
        news_json = json.dumps(report.key_concerns) if report.key_concerns else "[]"
        
        prompt = get_talking_points_prompt(
            company_name=company.name or "Unknown Company",
            rating=report.rating or "N/A",
            summary=report.summary or "No summary available.",
            financial_analysis=financial_json,
            claims_analysis=claims_json, 
            news_analysis=news_json
        )

        llm = get_llm("llama-3.1-8b-instant")
        response = llm.invoke([
            SystemMessage(content=TALKING_POINTS_SYSTEM),
            HumanMessage(content=prompt)
        ])
        
        # Parse JSON response
        content = response.content
        print(f"LLM Raw Response: {content}") # Log for debugging
        
        # Robust extraction: find the first outer { and last }
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                talking_points = json.loads(json_str)
            except json.JSONDecodeError as je:
                print(f"JSON Parse Error on extracted string: {je}")
                # Try to clean it up (sometimes there are trailing commas)
                raise ValueError(f"Extracted JSON was invalid: {je}")
        else:
             # If no brackets found, it might be raw text or empty
             if not content.strip():
                 raise ValueError("LLM returned empty response")
             raise ValueError("Could not find JSON structure in LLM response")
        
        # Save to report
        report.talking_points = talking_points
        session.add(report)
        session.commit()
        session.refresh(report)
        
        return report.talking_points
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error generating talking points: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate talking points: {str(e)}")

@router.put("/report/{report_id}/talking-points")
def update_talking_points(
    report_id: UUID,
    talking_points: dict, 
    session: Session = Depends(get_session)
):
    """
    Updates the talking points for a specific analysis report (manual save/edit).
    """
    report = session.get(AnalysisReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.talking_points = talking_points
    session.add(report)
    session.commit()
    session.refresh(report)

    return report.talking_points
