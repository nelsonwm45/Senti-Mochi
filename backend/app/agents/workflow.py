"""
Multi-Agent Analysis Workflow

Orchestrates the Citation-First Analysis Engine using LangGraph.
The workflow consists of three main phases:
1. Intelligence Gathering - Agents collect data with citations
2. Cross-Examination - Agents critique each other's findings
3. Synthesis - Judge agent generates final decision with citation verification

The citation_registry is propagated through all phases, accumulating source metadata.
"""

from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.news_agent import news_agent, news_critique, news_defense
from app.agents.financial_agent import financial_agent, financial_critique, financial_defense
from app.agents.claims_agent import claims_agent, claims_critique
from app.agents.judge import judge_agent
from app.models import AnalysisStatus
from uuid import UUID
import time
from typing import Dict, Any


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


def merge_citation_registries(current: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge citation registries, with new entries overriding existing ones.

    Args:
        current: The current citation registry
        new: New entries to merge in

    Returns:
        Merged citation registry
    """
    merged = dict(current) if current else {}
    if new:
        merged.update(new)
    return merged


def gather_intelligence(state: AgentState) -> Dict[str, Any]:
    """
    Phase 1: Runs worker agents sequentially to gather intelligence.

    Each agent:
    1. Fetches relevant data
    2. Generates citations with [N#], [F#], [D#] format
    3. Returns analysis with citation_registry updates

    The citation_registry is merged across all agents.
    """
    job_id = state.get('job_id')
    print("Orchestrator: Starting sequential intelligence gathering...")

    # Initialize citation registry if not present
    citation_registry = dict(state.get('citation_registry', {}))

    # === NEWS AGENT ===
    update_job_progress(job_id, AnalysisStatus.GATHERING_INTEL, "Analyzing news articles [N#]", 15)
    start = time.time()
    news_result = news_agent(state)
    print(f"News agent completed in {time.time() - start:.2f}s")

    # Merge news citations
    if 'citation_registry' in news_result:
        citation_registry = merge_citation_registries(citation_registry, news_result['citation_registry'])

    # Update state for next agent
    state_with_citations = {**state, 'citation_registry': citation_registry}

    # === FINANCIAL AGENT ===
    update_job_progress(job_id, AnalysisStatus.GATHERING_INTEL, "Processing financial data [F#]", 30)
    start = time.time()
    fin_result = financial_agent(state_with_citations)
    print(f"Financial agent completed in {time.time() - start:.2f}s")

    # Merge financial citations
    if 'citation_registry' in fin_result:
        citation_registry = merge_citation_registries(citation_registry, fin_result['citation_registry'])

    # Update state for next agent
    state_with_citations = {**state, 'citation_registry': citation_registry}

    # === CLAIMS AGENT ===
    update_job_progress(job_id, AnalysisStatus.GATHERING_INTEL, "Analyzing documents & claims [D#]", 45)
    start = time.time()
    claims_result = claims_agent(state_with_citations)
    print(f"Claims agent completed in {time.time() - start:.2f}s")
    print(f"Orchestrator: Claims returned registry keys: {list(claims_result.get('citation_registry', {}).keys())}")

    # Merge claims citations
    if 'citation_registry' in claims_result:
        citation_registry = merge_citation_registries(citation_registry, claims_result['citation_registry'])
        print(f"Orchestrator: Merged registry keys: {list(citation_registry.keys())}")

    # Build combined update
    update = {
        'citation_registry': citation_registry
    }

    # Add analysis results (excluding citation_registry to avoid duplication)
    for key, value in news_result.items():
        if key != 'citation_registry':
            update[key] = value

    for key, value in fin_result.items():
        if key != 'citation_registry':
            update[key] = value

    for key, value in claims_result.items():
        if key != 'citation_registry':
            update[key] = value

    print(f"Orchestrator: Intelligence gathering complete. Citation registry has {len(citation_registry)} entries.")

    return update


def cross_examination(state: AgentState) -> Dict[str, Any]:
    """
    Phase 2: Agents critique each other's findings.

    Critique agents preserve and reference citation IDs from Phase 1.
    The debate phase builds government (pro) and opposition (skeptic) arguments.
    """
    job_id = state.get('job_id')
    print("Orchestrator: Starting debate/critique phase...")

    # Citation registry should already be populated from Phase 1
    citation_registry = dict(state.get('citation_registry', {}))
    print(f"Cross-examination starting with {len(citation_registry)} citations in registry")

    # === NEWS CRITIQUE (Opposition role) ===
    update_job_progress(job_id, AnalysisStatus.CROSS_EXAMINATION, "Cross-examining findings (News)", 55)
    start = time.time()
    news_critique_result = news_critique(state)
    print(f"News critique completed in {time.time() - start:.2f}s")

    # === FINANCIAL CRITIQUE (Government role) ===
    update_job_progress(job_id, AnalysisStatus.CROSS_EXAMINATION, "Cross-examining findings (Financial)", 65)
    start = time.time()
    fin_critique_result = financial_critique(state)
    print(f"Financial critique completed in {time.time() - start:.2f}s")

    # === CLAIMS CRITIQUE (Objective role) ===
    update_job_progress(job_id, AnalysisStatus.CROSS_EXAMINATION, "Cross-examining findings (Claims)", 75)
    start = time.time()
    claims_critique_result = claims_critique(state)
    print(f"Claims critique completed in {time.time() - start:.2f}s")

    # Combine updates
    update = {}
    update.update(news_critique_result)
    update.update(fin_critique_result)
    update.update(claims_critique_result)

    # Extract debate arguments for the judge
    # Government arguments come from Financial (pro-company)
    # Opposition arguments come from News (skeptic)
    government_arguments = []
    opposition_arguments = []

    # Parse critique outputs for structured debate content
    if fin_critique_result.get('financial_critique'):
        government_arguments.append(fin_critique_result['financial_critique'])

    if news_critique_result.get('news_critique'):
        opposition_arguments.append(news_critique_result['news_critique'])

    update['government_arguments'] = government_arguments
    update['opposition_arguments'] = opposition_arguments

    return update


def defense_phase(state: AgentState) -> Dict[str, Any]:
    """
    Phase 3: Rebuttal/Defense Phase (New).
    Government defends against News Critique.
    Opposition rebuts Financial Critique.
    """
    job_id = state.get('job_id')
    print("Orchestrator: Starting defense/rebuttal phase...")

    # === FINANCIAL DEFENSE (Government defending) ===
    update_job_progress(job_id, AnalysisStatus.CROSS_EXAMINATION, "Government Defense (Financial)", 80)
    start = time.time()
    fin_defense_result = financial_defense(state)
    print(f"Financial defense completed in {time.time() - start:.2f}s")

    # === NEWS DEFENSE (Opposition rebutting) ===
    update_job_progress(job_id, AnalysisStatus.CROSS_EXAMINATION, "Opposition Rebuttal (News)", 82)
    start = time.time()
    news_defense_result = news_defense(state)
    print(f"News defense completed in {time.time() - start:.2f}s")

    # Combine updates
    update = {}
    update.update(fin_defense_result)
    update.update(news_defense_result)

    # Append to arguments for Judge
    gov_args = state.get('government_arguments', []) or []
    opp_args = state.get('opposition_arguments', []) or []

    if fin_defense_result.get('financial_defense'):
        gov_args.append(fin_defense_result['financial_defense'])
    
    if news_defense_result.get('news_defense'):
        opp_args.append(news_defense_result['news_defense'])

    update['government_arguments'] = gov_args
    update['opposition_arguments'] = opp_args

    return update


def judge_with_status(state: AgentState) -> Dict[str, Any]:
    """
    Phase 3: Judge synthesizes all findings into final decision.

    The Judge:
    1. Receives the complete citation_registry from Phases 1-2
    2. Synthesizes with role-specific decision logic
    3. Verifies citations (hallucination check)
    4. Generates FinalAnalysisOutput
    """
    job_id = state.get('job_id')
    update_job_progress(job_id, AnalysisStatus.SYNTHESIZING, "Synthesizing final report", 85)

    citation_registry = state.get('citation_registry', {})
    print(f"Judge receiving {len(citation_registry)} citations in registry")

    start = time.time()
    result = judge_agent(state)
    print(f"Judge agent completed in {time.time() - start:.2f}s")

    # Check for hallucinations
    hallucinated = result.get('hallucinated_citations', [])
    if hallucinated:
        print(f"CITATION VERIFICATION: {len(hallucinated)} hallucinated citations detected: {hallucinated}")

    update_job_progress(job_id, AnalysisStatus.EMBEDDING, "Embedding report for search", 95)

    return result


def build_graph():
    """
    Constructs the Multi-Agent Citation-First Analysis workflow graph.

    Flow:
    1. gather_intelligence -> Collect data with [N#], [F#], [D#] citations
    2. cross_examination -> Debate phase with citation preservation
    3. judge -> Final synthesis with hallucination check

    The citation_registry propagates through all phases.
    """
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node("gather_intelligence", gather_intelligence)
    builder.add_node("cross_examination", cross_examination)
    builder.add_node("defense", defense_phase)
    builder.add_node("judge", judge_with_status)

    # Set entry point
    builder.set_entry_point("gather_intelligence")

    # Define edges (sequential flow)
    builder.add_edge("gather_intelligence", "cross_examination")
    builder.add_edge("cross_examination", "defense")
    builder.add_edge("defense", "judge")
    builder.add_edge("judge", END)

    return builder.compile()


# Global compiled graph
app_workflow = build_graph()


def run_analysis(
    company_id: str,
    company_name: str,
    analysis_persona: str,
    job_id: str = None
) -> Dict[str, Any]:
    """
    Run the complete analysis workflow.

    Args:
        company_id: UUID of the company to analyze
        company_name: Name of the company
        analysis_persona: User persona (INVESTOR, RELATIONSHIP_MANAGER, CREDIT_RISK, MARKET_ANALYST)
        job_id: Optional job ID for status tracking

    Returns:
        Complete analysis result with FinalAnalysisOutput
    """
    initial_state: AgentState = {
        'company_id': company_id,
        'company_name': company_name,
        'job_id': job_id,
        'analysis_persona': analysis_persona,
        'citation_registry': {},  # Initialize empty registry
        'news_data': None,
        'financial_data': None,
        'claims_data': None,
        'news_analysis': None,
        'financial_analysis': None,
        'claims_analysis': None,
        'news_critique': None,
        'financial_critique': None,
        'claims_critique': None,
        'government_arguments': None,
        'opposition_arguments': None,
        'final_report': None,
        'final_output_json': None,
        'errors': [],
        'hallucinated_citations': []
    }

    print(f"Starting Citation-First Analysis for {company_name} [{analysis_persona}]")

    result = app_workflow.invoke(initial_state)

    print(f"Analysis complete. Final citation count: {len(result.get('citation_registry', {}))}")

    return result
