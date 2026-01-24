
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.news_agent import news_agent
from app.agents.financial_agent import financial_agent
from app.agents.claims_agent import claims_agent
from app.agents.judge import judge_agent
from app.models import AnalysisStatus
from uuid import UUID
import time

def update_job_progress(job_id: str, status: AnalysisStatus, step: str, progress: int):
    """Update job status in the database."""
    if not job_id:
        return

    from app.database import engine
    from sqlmodel import Session
    from app.models import AnalysisJob

    try:
        with Session(engine) as session:
            job = session.get(AnalysisJob, UUID(job_id))
            if job:
                job.status = status
                job.current_step = step
                job.progress = progress
                session.add(job)
                session.commit()
    except Exception as e:
        print(f"Failed to update job progress: {e}")

def gather_intelligence(state: AgentState):
    """
    Runs worker agents sequentially to avoid Rate Limits.
    """
    job_id = state.get('job_id')
    print("Orchestrator: Starting sequential intelligence gathering...")

    # Update status for each agent
    update_job_progress(job_id, AnalysisStatus.GATHERING_INTEL, "Analyzing news articles", 15)
    start = time.time()
    news_result = news_agent(state)
    print(f"News agent completed in {time.time() - start:.2f}s")

    update_job_progress(job_id, AnalysisStatus.GATHERING_INTEL, "Processing financial data", 30)
    start = time.time()
    fin_result = financial_agent(state)
    print(f"Financial agent completed in {time.time() - start:.2f}s")

    update_job_progress(job_id, AnalysisStatus.GATHERING_INTEL, "Analyzing documents & claims", 45)
    start = time.time()
    claims_result = claims_agent(state)
    print(f"Claims agent completed in {time.time() - start:.2f}s")

    update = {}
    update.update(news_result)
    update.update(fin_result)
    update.update(claims_result)

    return update

def cross_examination(state: AgentState):
    """
    Second Phase: Agents critique each other.
    Runs sequentially.
    """
    job_id = state.get('job_id')
    print("Orchestrator: Starting debate/critique phase...")
    from app.agents.news_agent import news_critique
    from app.agents.financial_agent import financial_critique
    from app.agents.claims_agent import claims_critique

    update_job_progress(job_id, AnalysisStatus.CROSS_EXAMINATION, "Cross-examining findings (News)", 55)
    start = time.time()
    news_critique_result = news_critique(state)
    print(f"News critique completed in {time.time() - start:.2f}s")

    update_job_progress(job_id, AnalysisStatus.CROSS_EXAMINATION, "Cross-examining findings (Financial)", 65)
    start = time.time()
    fin_critique_result = financial_critique(state)
    print(f"Financial critique completed in {time.time() - start:.2f}s")

    update_job_progress(job_id, AnalysisStatus.CROSS_EXAMINATION, "Cross-examining findings (Claims)", 75)
    start = time.time()
    claims_critique_result = claims_critique(state)
    print(f"Claims critique completed in {time.time() - start:.2f}s")

    update = {}
    update.update(news_critique_result)
    update.update(fin_critique_result)
    update.update(claims_critique_result)

    return update

def judge_with_status(state: AgentState):
    """Wrapper for judge_agent that updates status."""
    job_id = state.get('job_id')
    update_job_progress(job_id, AnalysisStatus.SYNTHESIZING, "Synthesizing final report", 85)
    start = time.time()
    result = judge_agent(state)
    print(f"Judge agent completed in {time.time() - start:.2f}s")
    update_job_progress(job_id, AnalysisStatus.EMBEDDING, "Embedding report for search", 95)
    return result

def build_graph():
    """
    Constructs the Multi-Agent workflow graph.
    """
    builder = StateGraph(AgentState)

    builder.add_node("gather_intelligence", gather_intelligence)
    builder.add_node("cross_examination", cross_examination)
    builder.add_node("judge", judge_with_status)

    builder.set_entry_point("gather_intelligence")

    builder.add_edge("gather_intelligence", "cross_examination")
    builder.add_edge("cross_examination", "judge")
    builder.add_edge("judge", END)

    return builder.compile()

# Global compiled graph
app_workflow = build_graph()
