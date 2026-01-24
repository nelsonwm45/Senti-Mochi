
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from app.auth import get_current_user
from pydantic import BaseModel, Field
from sqlmodel import Session, select, col
from app.database import get_session
from app.models import Company, AnalysisReport, AnalysisJob, AnalysisStatus
from app.agents.workflow import app_workflow, MAX_LOOPS
from app.agents.state import AgentState
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum

router = APIRouter()


# ============================================================
# FEATURE 5: Request Models with User Role
# ============================================================

class UserRoleEnum(str, Enum):
    """Polymorphic analysis personas"""
    INVESTOR = "investor"
    CREDIT_RISK = "credit_risk"
    RELATIONSHIP_MANAGER = "relationship_manager"
    MARKET_ANALYST = "market_analyst"


class AnalysisRequest(BaseModel):
    """Request body for triggering analysis with optional user role"""
    user_role: UserRoleEnum = Field(
        default=UserRoleEnum.INVESTOR,
        description="User persona for polymorphic analysis: investor, credit_risk, or relationship_manager"
    )
    max_loops: int = Field(
        default=MAX_LOOPS,
        ge=0,
        le=5,
        description="Maximum research loopbacks (0-5, default 3)"
    )


class AnalysisResponse(BaseModel):
    """Response model for analysis trigger"""
    message: str
    company_id: UUID
    job_id: UUID
    user_role: str
    status: Optional[AnalysisStatus] = None


class JobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: UUID
    company_id: Optional[UUID] = None
    status: AnalysisStatus
    current_step: Optional[str] = None
    progress: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    report_id: Optional[UUID] = None


# ============================================================
# Helper Functions
# ============================================================

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


# ============================================================
# API Endpoints
# ============================================================

@router.post("/{company_id}", status_code=202, response_model=AnalysisResponse)
def trigger_analysis(
    company_id: UUID,
    background_tasks: BackgroundTasks,
    request: Optional[AnalysisRequest] = None,
    current_user: "User" = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Triggers the Multi-Agent Investment Analysis for a company.

    FEATURE 5: Accepts user_role for polymorphic analysis:
    - investor: Focus on growth, stock price, market sentiment (default)
    - credit_risk: Focus on debt ratios, cash flow, bankruptcy risk
    - relationship_manager: Focus on talking points, news, relationship opportunities

    Returns a job_id for status tracking.
    """
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Parse request or use defaults
    if request is None:
        request = AnalysisRequest()

    # Determine role: Explicit Request > User Preference > Default
    user_role = request.user_role.value if request.user_role else (current_user.persona or "investor")
    
    max_loops = request.max_loops

    # Check for existing running analysis
    existing_job = session.exec(
        select(AnalysisJob)
        .where(AnalysisJob.company_id == company_id)
        .where(AnalysisJob.status.not_in([AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]))
    ).first()

    if existing_job:
        return AnalysisResponse(
            message="Analysis already in progress",
            company_id=company_id,
            job_id=existing_job.id,
            user_role=user_role,
            status=existing_job.status
        )

    # Create new analysis job
    job = AnalysisJob(
        company_id=company_id,
        status=AnalysisStatus.PENDING,
        current_step=f"Initializing analysis (Role: {user_role.replace('_', ' ').title()})",
        progress=0
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    def run_workflow():
        from app.database import engine
        from sqlmodel import Session as SyncSession

        print(f"Starting analysis for {company.name} (Job: {job.id}, Role: {user_role})")
        try:
            # Update status: Starting
            with SyncSession(engine) as db:
                update_job_status(db, job.id, AnalysisStatus.GATHERING_INTEL, "Gathering intelligence", 10)

            # FEATURE 5: Pass user_role to initial state
            initial_state = {
                "company_id": str(company.id),
                "company_name": company.name,
                "job_id": str(job.id),
                "user_role": user_role,  # Polymorphic analysis
                "max_loops": max_loops,  # Judge-Loop configuration
                "loop_count": 0,
                "sources": [],
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
                    f"Analysis complete (Role: {user_role.replace('_', ' ').title()})",
                    100,
                    report_id=latest_report.id if latest_report else None
                )

            print(f"Workflow finished for {company.name}")
        except Exception as e:
            print(f"Workflow failed: {e}")
            import traceback
            traceback.print_exc()
            with SyncSession(engine) as db:
                update_job_status(db, job.id, AnalysisStatus.FAILED, "Analysis failed", error_message=str(e))

    background_tasks.add_task(run_workflow)

    return AnalysisResponse(
        message="Analysis started",
        company_id=company_id,
        job_id=job.id,
        user_role=user_role
    )


@router.get("/{company_id}/status", response_model=JobStatusResponse)
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
        raise HTTPException(
            status_code=404,
            detail="No analysis has been run for this company"
        )

    return JobStatusResponse(
        job_id=job.id,
        company_id=job.company_id,
        status=job.status,
        current_step=job.current_step,
        progress=job.progress,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
        report_id=job.report_id
    )


@router.get("/job/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: UUID, session: Session = Depends(get_session)):
    """
    Get the status of a specific analysis job.
    """
    job = session.get(AnalysisJob, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.id,
        company_id=job.company_id,
        status=job.status,
        current_step=job.current_step,
        progress=job.progress,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
        report_id=job.report_id
    )


@router.get("/{company_id}/reports")
def get_reports(
    company_id: UUID,
    limit: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """
    Retrieves analysis reports for a company.
    Returns reports with verdict and sources information.
    """
    statement = (
        select(AnalysisReport)
        .where(AnalysisReport.company_id == company_id)
        .order_by(col(AnalysisReport.created_at).desc())
        .limit(limit)
    )
    reports = session.exec(statement).all()

    # Enhance response with verdict extraction from agent_logs
    enhanced_reports = []
    for report in reports:
        report_dict = {
            "id": report.id,
            "company_id": report.company_id,
            "rating": report.rating,
            "confidence_score": report.confidence_score,
            "summary": report.summary,
            "bull_case": report.bull_case,
            "bear_case": report.bear_case,
            "risk_factors": report.risk_factors,
            "esg_analysis": report.esg_analysis,
            "financial_analysis": report.financial_analysis,
            "created_at": report.created_at,
        }

        # Extract verdict and sources from agent_logs
        if report.agent_logs:
            for log in report.agent_logs:
                if log.get("agent") == "verdict":
                    report_dict["verdict"] = log.get("output")
                elif log.get("agent") == "sources":
                    report_dict["sources"] = log.get("output")
                elif log.get("agent") == "user_role":
                    report_dict["user_role"] = log.get("output")
                elif log.get("agent") == "debate":
                    report_dict["debate"] = {
                        "bull_arguments": log.get("bull", []),
                        "bear_arguments": log.get("bear", []),
                        "evidence_clashes": log.get("clashes", [])
                    }

        enhanced_reports.append(report_dict)

    return enhanced_reports


@router.get("/report/{report_id}")
def get_report(report_id: UUID, session: Session = Depends(get_session)):
    """
    Retrieves a specific analysis report with full details.
    Includes verdict, sources, and debate synthesis.
    """
    report = session.get(AnalysisReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    response = {
        "id": report.id,
        "company_id": report.company_id,
        "rating": report.rating,
        "confidence_score": report.confidence_score,
        "summary": report.summary,
        "bull_case": report.bull_case,
        "bear_case": report.bear_case,
        "risk_factors": report.risk_factors,
        "esg_analysis": report.esg_analysis,
        "financial_analysis": report.financial_analysis,
        "created_at": report.created_at,
        "agent_logs": report.agent_logs,
    }

    # Extract structured data from agent_logs
    if report.agent_logs:
        for log in report.agent_logs:
            if log.get("agent") == "verdict":
                response["verdict"] = log.get("output")
            elif log.get("agent") == "sources":
                response["sources"] = log.get("output")
            elif log.get("agent") == "user_role":
                response["user_role"] = log.get("output")
            elif log.get("agent") == "debate":
                response["debate_synthesis"] = {
                    "bull_arguments": log.get("bull", []),
                    "bear_arguments": log.get("bear", []),
                    "evidence_clashes": log.get("clashes", [])
                }

    return response


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


# ============================================================
# Additional Endpoints for New Features
# ============================================================

@router.get("/roles")
def get_available_roles():
    """
    Returns available user roles for polymorphic analysis.
    FEATURE 5: Explains what each role focuses on.
    """
    return {
        "roles": [
            {
                "id": "investor",
                "name": "Investor",
                "description": "Focus on growth, stock price, market sentiment, and profitability trends",
                "weights": {
                    "growth": 0.30,
                    "profitability": 0.25,
                    "debt_health": 0.15,
                    "esg": 0.15,
                    "sentiment": 0.15
                }
            },
            {
                "id": "credit_risk",
                "name": "Credit Risk Stakeholder",
                "description": "Focus on debt ratios, cash flow stability, and bankruptcy risk indicators",
                "weights": {
                    "growth": 0.10,
                    "profitability": 0.20,
                    "debt_health": 0.40,
                    "esg": 0.15,
                    "sentiment": 0.15
                }
            },
            {
                "id": "relationship_manager",
                "name": "Relationship Manager",
                "description": "Focus on talking points, recent news, and relationship-building opportunities",
                "weights": {
                    "growth": 0.15,
                    "profitability": 0.15,
                    "debt_health": 0.15,
                    "esg": 0.20,
                    "sentiment": 0.35
                }
            },
            {
                "id": "market_analyst",
                "name": "Market Analyst",
                "description": "Focus on peer comparison, macro trends, and relative valuation",
                "weights": {
                    "growth": 0.20,
                    "profitability": 0.20,
                    "debt_health": 0.20,
                    "esg": 0.20,
                    "sentiment": 0.20
                }
            }
        ]
    }
