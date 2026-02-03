"""
Financial Agent - The Accountant

Analyzes financial statements with citation tracking.
Generates [F1], [F2], [F3], ... citations mapping to {document_name, row_line}.
Focus: Valuation, Profitability, Growth, Financial Health.
"""

from typing import Dict, Any, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import FinancialStatement
from app.agents.base import get_llm
from app.agents.state import AgentState
from app.agents.cache import generate_cache_key, hash_content, get_cached_result, set_cached_result
from app.agents.persona_config import get_persona_config
from app.agents.prompts import FINANCIAL_AGENT_SYSTEM, get_financial_agent_prompt, get_critique_prompt, get_defense_prompt
from app.agents.citation_models import SourceMetadata
from langchain_core.messages import SystemMessage, HumanMessage
import json


# Mapping of statement types to citation IDs
STATEMENT_TYPE_CITATION_MAP = {
    "income_statement": "F1",
    "balance_sheet": "F2",
    "cash_flow": "F3",
}


def financial_agent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes financial statements with citation tracking.

    Citation Protocol:
    - [F1] -> Income Statement
    - [F2] -> Balance Sheet
    - [F3] -> Cash Flow Statement
    - Additional sources get [F4], [F5], etc.

    Returns:
        Dict with financial_analysis and citation_registry updates
    """
    persona = state.get('analysis_persona', 'INVESTOR')
    config = get_persona_config(persona)
    company_id = state["company_id"]
    company_name = state["company_name"]

    print(f"Financial Agent: Analyzing for {company_name} [Persona: {persona}]")

    # Initialize citation registry if not present
    citation_registry = dict(state.get('citation_registry', {}))

    with Session(engine) as session:
        # Fetch detailed statements
        statement = (
            select(FinancialStatement)
            .where(FinancialStatement.company_id == company_id)
            .order_by(col(FinancialStatement.period).desc())
        )
        financials = session.exec(statement).all()

        if not financials:
            return {
                "financial_analysis": "No financial data found.",
                "citation_registry": citation_registry
            }

        # Organize by type and create citation metadata
        data_summary = {}
        source_list_parts = []
        next_citation_idx = 4  # Start at F4 for additional sources

        for f in financials:
            st_type = f.statement_type.lower()

            # Get or assign citation ID
            if st_type in STATEMENT_TYPE_CITATION_MAP:
                citation_id = STATEMENT_TYPE_CITATION_MAP[st_type]
            else:
                citation_id = f"F{next_citation_idx}"
                next_citation_idx += 1

            # Create SourceMetadata for this statement (only once per type)
            if citation_id not in citation_registry:
                source_metadata = {
                    "id": citation_id,
                    "title": f"{st_type.replace('_', ' ').title()} ({f.period})",
                    "url_or_path": f"financial_statement/{f.id}",
                    "type": "Financial",
                    "date": f.period,
                    "row_line": f"Period: {f.period}"
                }
                citation_registry[citation_id] = source_metadata

                # Add to source list for prompt
                source_list_parts.append(
                    f"[{citation_id}] - {st_type.replace('_', ' ').title()} (Period: {f.period})"
                )

            # Organize data
            if st_type not in data_summary:
                data_summary[st_type] = []
            data_summary[st_type].append({
                "period": f.period,
                "data": f.data,
                "citation_id": citation_id
            })

    # Prepare context with embedded citation references
    context_parts = []
    for st_type, records in data_summary.items():
        # Sort by period descending
        records.sort(key=lambda x: x['period'], reverse=True)
        recent_records = records[:3]

        # Get the citation ID for this statement type
        citation_id = STATEMENT_TYPE_CITATION_MAP.get(st_type, records[0]['citation_id'])

        context_parts.append(f"### {st_type.upper()} [{citation_id}]")
        for r in recent_records:
            context_parts.append(f"Period: {r['period']}")
            context_parts.append(json.dumps(r['data'], indent=2))

    context = "\n".join(context_parts)
    source_list = "\n".join(source_list_parts)

    # Generate cache key based on content hash
    content_hash = hash_content(context)
    cache_key = generate_cache_key("financial_v4", company_id, content_hash)

    # Check cache first
    cached_result = get_cached_result(cache_key)
    if cached_result:
        return {
            "financial_analysis": cached_result,
            "citation_registry": citation_registry
        }

    # Truncate if too long
    # Truncation Logic with Fallback Strategy
    full_context = context

    # Attempt Primary: Cerebras (llama-3.3-70b)
    try:
        print(f"[Financial Agent] Attempting to use Cerebras (llama-3.3-70b)...")
        prompt = get_financial_agent_prompt(
            company_name=company_name,
            persona=persona,
            financial_context=full_context,
            source_list=source_list
        )

        llm = get_llm("llama-3.3-70b")
        response = llm.invoke([
            SystemMessage(content=FINANCIAL_AGENT_SYSTEM),
            HumanMessage(content=prompt)
        ])
        print(f"[Financial Agent] SUCCESS: Processed by Cerebras (llama-3.3-70b)")
        
        set_cached_result(cache_key, response.content)

        return {
            "financial_analysis": response.content,
            "citation_registry": citation_registry
        }

    except Exception as e:
        print(f"[Financial Agent] Cerebras failed: {e}. Fallback to Groq (llama-3.1-8b-instant)...")
        
        # Apply truncation for Groq (4500 chars)
        if len(full_context) > 4500:
            truncated_context = full_context[:4500] + "... [TRUNCATED]"
        else:
            truncated_context = full_context

        prompt = get_financial_agent_prompt(
            company_name=company_name,
            persona=persona,
            financial_context=truncated_context,
            source_list=source_list
        )

        llm = get_llm("llama-3.1-8b-instant")
        response = llm.invoke([
            SystemMessage(content=FINANCIAL_AGENT_SYSTEM),
            HumanMessage(content=prompt)
        ])
        print(f"[Financial Agent] SUCCESS: Processed by Groq (llama-3.1-8b-instant)")

        set_cached_result(cache_key, response.content)

        return {
            "financial_analysis": response.content,
            "citation_registry": citation_registry
        }


def financial_critique(state: AgentState) -> Dict[str, Any]:
    """
    Critiques other agents' findings based on Financial data.
    Preserves and references all citation IDs.
    """
    persona = state.get('analysis_persona', 'INVESTOR')
    persona_label = persona.replace('_', ' ').title()
    print(f"Financial Agent: Critiquing findings for {state['company_name']} [Persona: {persona}]")

    news_analysis = state.get("news_analysis", "No news analysis provided.")
    claims_analysis = state.get("claims_analysis", "No claims analysis provided.")
    my_analysis = state.get("financial_analysis", "No financial analysis provided.")

    prompt = get_critique_prompt(
        agent_type="financial",
        persona=persona,
        my_analysis=my_analysis,
        other_analysis_1=news_analysis,
        other_analysis_2=claims_analysis,
        analysis_1_name="News Analysis",
        analysis_2_name="Claims Analysis"
    )

    system_msg = f"You are a sharp financial analyst serving a {persona_label}. PRESERVE all citation IDs."

    # Attempt Primary: Cerebras
    try:
        print(f"[Financial Agent] Critique: Attempting Cerebras (llama-3.3-70b)...")
        llm = get_llm("llama-3.3-70b")
        response = llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt)
        ])
        print(f"[Financial Agent] Critique: SUCCESS (Cerebras)")
        return {"financial_critique": response.content}
    except Exception as e:
        print(f"[Financial Agent] Critique: Cerebras failed: {e}. Fallback to Groq...")
        llm = get_llm("llama-3.1-8b-instant")
        response = llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt)
        ])
        print(f"[Financial Agent] Critique: SUCCESS (Groq)")
        return {"financial_critique": response.content}

def financial_defense(state: AgentState) -> Dict[str, Any]:
    """
    Defends the Government position against Opposition critique.
    """
    persona = state.get('analysis_persona', 'INVESTOR')
    persona_label = persona.replace('_', ' ').title()
    print(f"Financial Agent: Defending against Opposition critique for {state['company_name']}")

    my_analysis = state.get("financial_analysis", "No financial analysis provided.")
    # Opposition critique is stored in 'news_critique' from the critique phase
    opposition_critique = state.get("news_critique", "No opposition critique provided.")

    prompt = get_defense_prompt(
        agent_type="financial",
        persona=persona,
        my_analysis=my_analysis,
        opponent_critique=opposition_critique
    )

    system_msg = f"You are the Government (Pro-Company) attempting to defend your financial thesis. PRESERVE [F#] citations."

    # Using Cerebras for strong reasoning
    try:
        llm = get_llm("llama-3.3-70b")
        response = llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt)
        ])
        print(f"[Financial Agent] Defense: SUCCESS")
        return {"financial_defense": response.content}
    except Exception as e:
        print(f"[Financial Agent] Defense: Failed {e}, fallback groq")
        llm = get_llm("llama-3.1-8b-instant")
        response = llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt)
        ])
        return {"financial_defense": response.content}
