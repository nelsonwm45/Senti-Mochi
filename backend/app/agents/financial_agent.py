
from typing import Dict, Any, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import FinancialStatement
from app.agents.base import get_llm
from app.agents.state import AgentState
from app.agents.cache import generate_cache_key, hash_content, get_cached_result, set_cached_result
from app.agents.persona_config import get_persona_config
from langchain_core.messages import SystemMessage, HumanMessage
import json

def financial_agent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes financial statements.
    Uses caching to ensure consistent results for unchanged data.
    Adapts focus based on analysis_persona.
    """
    persona = state.get('analysis_persona', 'INVESTOR')
    config = get_persona_config(persona)
    print(f"Financial Agent: Analyzing for company {state['company_name']} [Persona: {persona}]")

    with Session(engine) as session:
        # Fetch detailed statements
        statement = (
            select(FinancialStatement)
            .where(FinancialStatement.company_id == state["company_id"])
            .order_by(col(FinancialStatement.period).desc())
        )
        financials = session.exec(statement).all()

        if not financials:
            return {"financial_analysis": "No financial data found."}

        # Organize by type
        data_summary = {}
        for f in financials:
            if f.statement_type not in data_summary:
                data_summary[f.statement_type] = []
            data_summary[f.statement_type].append({
                "period": f.period,
                "data": f.data
            })

    # Prepare context
    context_parts = []
    for st_type, records in data_summary.items():
        # Sort by period descending
        records.sort(key=lambda x: x['period'], reverse=True)
        recent_records = records[:3]
        context_parts.append(f"### {st_type.upper()}")
        for r in recent_records:
            context_parts.append(f"Period: {r['period']}")
            context_parts.append(json.dumps(r['data'], indent=2))

    context = "\n".join(context_parts)

    # Generate cache key based on content hash
    content_hash = hash_content(context)
    cache_key = generate_cache_key("financial", state["company_id"], content_hash)

    # Check cache first
    cached_result = get_cached_result(cache_key)
    if cached_result:
        return {"financial_analysis": cached_result}

    # Check token limit roughly (characters / 4)
    # Reduced to 15000 to fit within Groq's 6000 TPM limit (approx 3750 tokens)
    if len(context) > 15000:
        context = context[:15000] + "..."

    # Build persona-specific prompt
    focus_metrics = ", ".join(config['financial_focus'])
    persona_label = persona.replace('_', ' ').title()

    prompt = f"""You are a Financial Analyst serving a {persona_label}.

    PRIORITY METRICS TO CALCULATE: {focus_metrics}

    Analyze the following financial statements for {state['company_name']}.
    Focus on calculating and assessing: {focus_metrics}

    Financial Data:
    {context}

    Provide a professional assessment in Markdown, prioritizing metrics most relevant to a {persona_label}."""

    llm = get_llm("llama-3.1-8b-instant")
    response = llm.invoke([SystemMessage(content="You are an expert financial analyst."), HumanMessage(content=prompt)])

    # Cache the result
    set_cached_result(cache_key, response.content)

    return {"financial_analysis": response.content}

def financial_critique(state: AgentState) -> Dict[str, Any]:
    """
    Critiques other agents' findings based on Financial data.
    Uses persona-specific debate stances.
    """
    persona = state.get('analysis_persona', 'INVESTOR')
    config = get_persona_config(persona)
    persona_label = persona.replace('_', ' ').title()
    print(f"Financial Agent: Critiquing findings for {state['company_name']} [Persona: {persona}]")

    news_analysis = state.get("news_analysis", "No news analysis provided.")
    claims_analysis = state.get("claims_analysis", "No claims analysis provided.")
    my_analysis = state.get("financial_analysis", "No financial analysis provided.")

    prompt = f"""You are a Financial Analyst in a structured debate for a {persona_label}.

    DEBATE CONTEXT:
    - GOVERNMENT (Pro) Stance: {config['government_stance']}
    - OPPOSITION (Skeptic) Stance: {config['opposition_stance']}

    You are playing the GOVERNMENT role. Use hard financial numbers to support or defend.

    Your Task:
    Critique the findings from the News Analyst and Claims Analyst based on actual financial data.
    - Point out where sentiment doesn't match financial reality.
    - Verify or challenge claims with hard numbers.
    - Highlight positive fundamentals if news/claims are overly negative.

    1. FINANCIAL ANALYSIS (Your Context):
    {my_analysis}

    2. NEWS ANALYSIS (To Critique):
    {news_analysis}

    3. CLAIMS ANALYSIS (To Critique):
    {claims_analysis}

    Provide a concise critique (max 200 words) applying the Government stance where relevant.
    """

    llm = get_llm("llama-3.1-8b-instant")
    response = llm.invoke([SystemMessage(content=f"You are a data-driven financial analyst serving a {persona_label}."), HumanMessage(content=prompt)])

    return {"financial_critique": response.content}
