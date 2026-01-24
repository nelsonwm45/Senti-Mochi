
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState, get_role_weights
from app.agents.news_agent import news_agent, news_debate
from app.agents.financial_agent import financial_agent, financial_debate
from app.agents.claims_agent import claims_agent, claims_debate
from app.agents.judge import judge_agent, evaluate_sufficiency
from app.models import AnalysisStatus
from uuid import UUID
import time

# ============================================================
# FEATURE 2: Judge-Loop Configuration
# ============================================================
MAX_LOOPS = 3  # Maximum research loopbacks allowed


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
    FEATURE 1: Now collects cited facts and sources.
    """
    job_id = state.get('job_id')
    loop_count = state.get('loop_count', 0)
    loopback = state.get('loopback_instruction')

    print(f"Orchestrator: Starting intelligence gathering (Loop {loop_count})...")

    # Initialize or preserve sources
    sources = state.get('sources', []) or []

    # Check if this is a targeted loopback
    if loopback and loop_count > 0:
        target = loopback.get('target_agent', '')
        query = loopback.get('research_query', '')
        print(f"Orchestrator: Targeted research loopback to {target}: {query}")

        update_job_progress(job_id, AnalysisStatus.GATHERING_INTEL, f"Research loopback: {target}", 40)

        # Only run the targeted agent
        if target == 'news':
            # Add research query to state for targeted search
            enhanced_state = {**state, 'research_query': query, 'sources': sources}
            result = news_agent(enhanced_state)
            return {**result, 'sources': result.get('sources', sources)}
        elif target == 'financial':
            enhanced_state = {**state, 'research_query': query, 'sources': sources}
            result = financial_agent(enhanced_state)
            return {**result, 'sources': result.get('sources', sources)}
        elif target == 'claims':
            enhanced_state = {**state, 'research_query': query, 'sources': sources}
            result = claims_agent(enhanced_state)
            return {**result, 'sources': result.get('sources', sources)}

    # Normal full intelligence gathering
    update_job_progress(job_id, AnalysisStatus.GATHERING_INTEL, "Analyzing news articles", 15)
    start = time.time()
    news_result = news_agent({**state, 'sources': sources})
    sources = news_result.get('sources', sources)
    print(f"News agent completed in {time.time() - start:.2f}s")

    update_job_progress(job_id, AnalysisStatus.GATHERING_INTEL, "Processing financial data", 30)
    start = time.time()
    fin_result = financial_agent({**state, 'sources': sources})
    sources = fin_result.get('sources', sources)
    print(f"Financial agent completed in {time.time() - start:.2f}s")

    update_job_progress(job_id, AnalysisStatus.GATHERING_INTEL, "Analyzing documents & claims", 45)
    start = time.time()
    claims_result = claims_agent({**state, 'sources': sources})
    sources = claims_result.get('sources', sources)
    print(f"Claims agent completed in {time.time() - start:.2f}s")

    update = {
        'sources': sources,
        'loop_count': loop_count
    }
    update.update(news_result)
    update.update(fin_result)
    update.update(claims_result)

    return update


def cross_examination(state: AgentState):
    """
    Second Phase: Agents engage in structured debate (Bull vs Bear).
    FEATURE 3: Outputs StructuredDebateOutput format.
    """
    job_id = state.get('job_id')
    print("Orchestrator: Starting structured debate phase...")

    update_job_progress(job_id, AnalysisStatus.CROSS_EXAMINATION, "News debate (Bull vs Bear)", 55)
    start = time.time()
    news_debate_result = news_debate(state)
    print(f"News debate completed in {time.time() - start:.2f}s")

    update_job_progress(job_id, AnalysisStatus.CROSS_EXAMINATION, "Financial debate (Bull vs Bear)", 65)
    start = time.time()
    fin_debate_result = financial_debate(state)
    print(f"Financial debate completed in {time.time() - start:.2f}s")

    update_job_progress(job_id, AnalysisStatus.CROSS_EXAMINATION, "Claims debate (Bull vs Bear)", 75)
    start = time.time()
    claims_debate_result = claims_debate(state)
    print(f"Claims debate completed in {time.time() - start:.2f}s")

    update = {}
    update.update(news_debate_result)
    update.update(fin_debate_result)
    update.update(claims_debate_result)

    return update


def judge_evaluation(state: AgentState):
    """
    FEATURE 2: Judge evaluates if data is sufficient for verdict.
    This is the decision point for the cyclic graph.
    """
    job_id = state.get('job_id')
    loop_count = state.get('loop_count', 0)
    max_loops = state.get('max_loops', MAX_LOOPS)

    print(f"Judge: Evaluating sufficiency (Loop {loop_count}/{max_loops})...")
    update_job_progress(job_id, AnalysisStatus.SYNTHESIZING, "Judge evaluating evidence", 80)

    # If we've hit max loops, proceed to finalization
    if loop_count >= max_loops:
        print(f"Judge: Max loops ({max_loops}) reached, proceeding to finalization")
        return {
            'needs_loopback': False,
            'judge_decision': 'sufficient',
            'loop_count': loop_count
        }

    # Evaluate sufficiency using the judge's assessment
    sufficiency_result = evaluate_sufficiency(state)

    decision = sufficiency_result.get('decision', 'sufficient')
    loopback_instruction = sufficiency_result.get('loopback_instruction')

    if decision == 'sufficient':
        print("Judge: Evidence sufficient, proceeding to verdict")
        return {
            'needs_loopback': False,
            'judge_decision': 'sufficient',
            'loop_count': loop_count
        }
    else:
        print(f"Judge: Evidence insufficient, requesting loopback to {decision}")
        return {
            'needs_loopback': True,
            'judge_decision': decision,
            'loopback_instruction': loopback_instruction,
            'loop_count': loop_count + 1  # Increment loop counter
        }


def judge_finalization(state: AgentState):
    """
    Final step: Judge synthesizes verdict with Flip Card UI format.
    FEATURE 4: Outputs verdict with headline and deep dive.
    FEATURE 5: Applies polymorphic weights based on user_role.
    """
    job_id = state.get('job_id')
    update_job_progress(job_id, AnalysisStatus.SYNTHESIZING, "Synthesizing final verdict", 85)

    start = time.time()
    result = judge_agent(state)
    print(f"Judge finalization completed in {time.time() - start:.2f}s")

    update_job_progress(job_id, AnalysisStatus.EMBEDDING, "Embedding report for search", 95)

    return result


def route_after_evaluation(state: AgentState) -> str:
    """
    FEATURE 2: Conditional edge router for Judge-Loop.
    Determines next node based on judge's evaluation.
    """
    needs_loopback = state.get('needs_loopback', False)
    decision = state.get('judge_decision', 'sufficient')

    if needs_loopback and decision != 'sufficient':
        print(f"Router: Looping back for more research ({decision})")
        return "gather_intelligence"  # Cycle back
    else:
        print("Router: Proceeding to finalization")
        return "judge_finalization"


def build_graph():
    """
    Constructs the Multi-Agent workflow graph with cyclic Judge-Loop.
    FEATURE 2: Implements conditional edges for research loopback.
    """
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node("gather_intelligence", gather_intelligence)
    builder.add_node("cross_examination", cross_examination)
    builder.add_node("judge_evaluation", judge_evaluation)
    builder.add_node("judge_finalization", judge_finalization)

    # Set entry point
    builder.set_entry_point("gather_intelligence")

    # Linear edges
    builder.add_edge("gather_intelligence", "cross_examination")
    builder.add_edge("cross_examination", "judge_evaluation")

    # FEATURE 2: Conditional edge for Judge-Loop
    builder.add_conditional_edges(
        "judge_evaluation",
        route_after_evaluation,
        {
            "gather_intelligence": "gather_intelligence",  # Loop back
            "judge_finalization": "judge_finalization"     # Proceed to verdict
        }
    )

    # Final edge to END
    builder.add_edge("judge_finalization", END)

    # Compile with recursion limit for safety
    return builder.compile()


# Global compiled graph
app_workflow = build_graph()
