
from typing import Dict, Any, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import FinancialStatement
from app.agents.base import get_llm
from app.agents.state import AgentState
from langchain_core.messages import SystemMessage, HumanMessage
import json

def financial_agent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes financial statements.
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
            # Append only key info to save tokens
            data_summary[f.statement_type].append({
                "period": f.period,
                "data": f.data # Assuming data isn't huge. If huge, we might need to select keys.
            })
            
    # Prepare context
    # We might want to limit to last 3 periods per type
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
    
    if len(context) > 25000:
        context = context[:25000] + "..."
        
    prompt = f"""You are a Financial Analyst. Analyze the following financial statements for {state['company_name']}.
    Calculate key ratios (Net Margin, PE if price available, Debt-to-Equity, etc.) where possible.
    Assess the financial health, growth trends, and stability.
    
    Financial Data:
    {context}
    
    Provide a professional financial assessment in Markdown."""
    
    llm = get_llm("llama3-70b-8192")
    response = llm.invoke([SystemMessage(content="You are an expert financial analyst."), HumanMessage(content=prompt)])
    
    return {"financial_analysis": response.content}
