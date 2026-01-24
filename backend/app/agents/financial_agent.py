
from typing import Dict, Any, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import FinancialStatement
from app.agents.base import get_llm
from app.agents.state import AgentState, CitedFact, SourceReference
from app.agents.cache import generate_cache_key, hash_content, get_cached_result, set_cached_result
from langchain_core.messages import SystemMessage, HumanMessage
import json


def financial_agent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes financial statements with full citation tracking.
    FEATURE 1: Every financial fact carries statement type, period, and source.
    """
    print(f"Financial Agent: Analyzing for company {state['company_name']}")
    
    # FEATURE 5: Polymorphic Analysis Focus
    user_role = state.get("user_role", "investor")
    
    role_focus_map = {
        "investor": "Focus on GROWTH & RETURNS: Revenue Growth (YoY), EPS Trends, Profit Margin Expansion, ROE, ROIC, Dividend Payout.",
        "relationship_manager": "Focus on ACTIVITY & SPENDING: Liquidity Events (cash raises), Capex Plans, large movements in Cash Flow.",
        "credit_risk": "Focus on SAFETY & SOLVENCY: Debt-to-Equity, Current Ratio, Interest Coverage, Altman Z-Score components.",
        "market_analyst": "Focus on VALUATION & QUALITY: DCF inputs, P/E vs Historical, Quality of Earnings (Cash Flow vs Net Income)."
    }
    focus_directive = role_focus_map.get(user_role, role_focus_map["investor"])
    print(f"Financial Focus ({user_role}): {focus_directive}")

    sources: List[dict] = state.get('sources', []) or []
    financial_facts: List[dict] = []
    statement_to_citation: Dict[str, str] = {}  # Map statement IDs to citation IDs

    with Session(engine) as session:
        # Fetch detailed statements
        statement = (
            select(FinancialStatement)
            .where(FinancialStatement.company_id == state["company_id"])
            .order_by(col(FinancialStatement.period).desc())
        )
        financials = session.exec(statement).all()

        if not financials:
            return {
                "financial_analysis": "No financial data found.",
                "financial_facts": [],
                "sources": sources
            }

        # Organize by type with citation tracking
        data_summary = {}
        fin_citation_counter = len([s for s in sources if s.get('type') == 'financial']) + 1

        for f in financials:
            # Create citation for this statement
            citation_id = f"F{fin_citation_counter}"
            fin_citation_counter += 1
            statement_to_citation[str(f.id)] = citation_id

            # Register source
            source_ref = SourceReference(
                id=citation_id,
                type="financial",
                title=f"{f.statement_type.replace('_', ' ').title()} - {f.period}",
                url=None,
                date=f.period
            )
            sources.append(source_ref.model_dump())

            if f.statement_type not in data_summary:
                data_summary[f.statement_type] = []

            data_summary[f.statement_type].append({
                "period": f.period,
                "data": f.data,
                "citation_id": citation_id
            })

            # Create cited fact for key metrics
            fact = CitedFact(
                content=f"{f.statement_type} for period {f.period}",
                source_url=None,
                source_title=f"{f.statement_type.replace('_', ' ').title()}",
                source_date=f.period,
                source_type="financial",
                confidence=0.95,
                citation_id=citation_id
            )
            financial_facts.append(fact.model_dump())

    # Prepare citation-aware context
    context_parts = []
    for st_type, records in data_summary.items():
        # Sort by period descending and take top 2 (reduced for token limits)
        records.sort(key=lambda x: x['period'], reverse=True)
        recent_records = records[:2]

        context_parts.append(f"### {st_type.upper()}")
        for r in recent_records:
            citation_id = r['citation_id']
            context_parts.append(f"[{citation_id}] Period: {r['period']}")

            # Truncate data JSON for token management
            data_str = json.dumps(r['data'], indent=2)
            if len(data_str) > 2000:
                data_str = data_str[:2000] + "..."
            context_parts.append(data_str)

    context = "\n".join(context_parts)

    # Generate cache key
    content_hash = hash_content(context)
    cache_key = generate_cache_key("financial_v2", state["company_id"], content_hash)

    # Check cache
    cached_result = get_cached_result(cache_key)
    if cached_result:
        try:
            cached_data = json.loads(cached_result)
            return {
                "financial_analysis": cached_data.get("analysis", cached_result),
                "financial_facts": cached_data.get("facts", financial_facts),
                "sources": cached_data.get("sources", sources)
            }
        except:
            return {"financial_analysis": cached_result, "financial_facts": financial_facts, "sources": sources}

    # Token limit management (Groq 6000 TPM)
    if len(context) > 10000:
        context = context[:10000] + "..."


    prompt = f"""You are a Financial Analyst. 
    ROLE FOCUS: {focus_directive}

    Analyze the following financial statements for {state['company_name']}.

    Financial Data:
    {context}
    
    Provide a professional financial assessment that includes:
    1. KEY METRICS (with citations)
       - Revenue, Net Income, EBITDA trends
       - Margins (Gross, Operating, Net)
    2. RATIOS (with citations)
       - PE Ratio (if price available)
       - Debt-to-Equity, Current Ratio
       - ROE, ROA
    3. FINANCIAL HEALTH ASSESSMENT (with citations)
    4. GROWTH TRENDS (with citations)
    
    IMPORTANT: Every financial claim MUST have a citation marker like [F1], [F2], etc.
    CRITICAL: Tailor the insights to the ROLE FOCUS provided above."""

    llm = get_llm("llama-3.1-8b-instant")
    response = llm.invoke([
        SystemMessage(content="You are an expert financial analyst. Always cite financial statements using [F1], [F2] format."),
        HumanMessage(content=prompt)
    ])

    analysis = response.content

    # Cache result with metadata
    cache_data = json.dumps({
        "analysis": analysis,
        "facts": financial_facts,
        "sources": sources
    })
    set_cached_result(cache_key, cache_data)

    return {
        "financial_analysis": analysis,
        "financial_facts": financial_facts,
        "sources": sources
    }


def financial_debate(state: AgentState) -> Dict[str, Any]:
    """
    FEATURE 3: Structured Debate - Financial Agent provides Bull/Bear arguments.
    """
    print(f"Financial Agent: Structured debate for {state['company_name']}")

    news_analysis = state.get("news_analysis", "No news analysis provided.")
    claims_analysis = state.get("claims_analysis", "No claims analysis provided.")
    my_analysis = state.get("financial_analysis", "No financial analysis provided.")

    # Truncate inputs for token limits
    if len(news_analysis) > 3000:
        news_analysis = news_analysis[:3000] + "..."
    if len(claims_analysis) > 3000:
        claims_analysis = claims_analysis[:3000] + "..."
    if len(my_analysis) > 3000:
        my_analysis = my_analysis[:3000] + "..."

    prompt = f"""You are a Financial Analyst participating in an investment debate.
    ROLE FOCUS: You are arguing from the perspective of a {state.get('user_role', 'investor')}.
    
    Based on the financial data and other analyses, construct a STRUCTURED DEBATE output.

1. FINANCIAL ANALYSIS (Your Context):
{my_analysis}

2. NEWS ANALYSIS:
{news_analysis}

3. CLAIMS/DOCUMENTS ANALYSIS:
{claims_analysis}

OUTPUT FORMAT (JSON):
{{
    "bull_argument": {{
        "claim": "Main bullish thesis from financial perspective (growth, profitability, etc.)",
        "supporting_facts": ["[F1]", "[F2]"],
        "strength": "strong|moderate|weak"
    }},
    "bear_argument": {{
        "claim": "Main bearish thesis (debt concerns, margin pressure, etc.)",
        "supporting_facts": ["[F1]"],
        "strength": "strong|moderate|weak"
    }},
    "evidence_clash": ["List where financials contradict news or claims"],
    "winning_side": "bull|bear|undecided",
    "reasoning": "Why this side is stronger based on financial evidence"
}}

Respond ONLY with valid JSON."""

    llm = get_llm("llama-3.1-8b-instant")
    response = llm.invoke([
        SystemMessage(content="You output structured JSON for investment debates based on financial analysis."),
        HumanMessage(content=prompt)
    ])

    # Parse response
    try:
        debate_output = json.loads(response.content)
    except:
        debate_output = {
            "bull_argument": {"claim": "Strong financial fundamentals", "supporting_facts": [], "strength": "moderate"},
            "bear_argument": {"claim": "Valuation concerns", "supporting_facts": [], "strength": "moderate"},
            "evidence_clash": [],
            "winning_side": "undecided",
            "reasoning": response.content[:500]
        }

    return {"financial_debate": debate_output, "financial_critique": response.content}


def financial_critique(state: AgentState) -> Dict[str, Any]:
    """
    Legacy critique function - now calls financial_debate for structured output.
    """
    return financial_debate(state)
