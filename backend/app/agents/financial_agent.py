
from typing import Dict, Any, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import FinancialStatement
from app.agents.base import get_llm
from app.agents.state import AgentState
from app.agents.cache import generate_cache_key, hash_content, get_cached_result, set_cached_result
from langchain_core.messages import SystemMessage, HumanMessage
import json

def financial_agent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes financial statements.
    Uses caching to ensure consistent results for unchanged data.
    """
    print(f"Financial Agent: Analyzing for company {state['company_name']}")

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

    if len(context) > 25000:
        context = context[:25000] + "..."

    prompt = f"""You are a Financial Analyst. Analyze the following financial statements for {state['company_name']}.
    Calculate key ratios (Net Margin, PE if price available, Debt-to-Equity, etc.) where possible.
    Assess the financial health, growth trends, and stability.

    Financial Data:
    {context}

    Provide a professional financial assessment in Markdown."""

    llm = get_llm("llama-3.3-70b-versatile")
    response = llm.invoke([SystemMessage(content="You are an expert financial analyst."), HumanMessage(content=prompt)])

    # Cache the result
    set_cached_result(cache_key, response.content)

    return {"financial_analysis": response.content}
