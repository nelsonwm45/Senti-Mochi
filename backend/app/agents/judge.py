
from typing import Dict, Any, Optional, Union, List
from enum import Enum
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.database import engine
from app.models import AnalysisReport, ReportChunk
from app.services.rag import RAGService
from app.agents.base import get_llm
from app.agents.state import AgentState, AnalysisPersona, get_role_weights, RoleWeights
from langchain_core.messages import SystemMessage, HumanMessage
import time
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Timeout configuration (in seconds)
LLM_TIMEOUT = 180  # 3 minutes for Judge Agent LLM call


class LLMTimeoutError(Exception):
    """Raised when LLM call exceeds timeout."""
    pass


def invoke_with_timeout(llm, messages, timeout_seconds):
    """Invoke LLM with a timeout using ThreadPoolExecutor."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(llm.invoke, messages)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeoutError:
            raise LLMTimeoutError(f"LLM call timed out after {timeout_seconds} seconds")


# ============================================================
# FEATURE 4: Verdict Models for Flip Card UI
# ============================================================

class VerdictAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Verdict(BaseModel):
    """FEATURE 4: Flip Card UI verdict format"""
    action: VerdictAction = Field(description="Investment action: BUY, SELL, or HOLD")
    headline_reasoning: str = Field(description="Short, punchy sentence for front of card (max 100 chars)")
    deep_dive_justification: str = Field(description="Detailed paragraph citing winning arguments for back of card")
    winning_debate_side: str = Field(default="undecided", description="'bull' or 'bear' - which side won")
    key_citations: List[str] = Field(default=[], description="Key citation IDs supporting the verdict")


# ============================================================
# Existing Models (Enhanced)
# ============================================================

class ESGTopic(BaseModel):
    score: int = Field(description="Score out of 100")
    summary: Optional[str] = Field(default="No summary available", description="Summary of performance in this area")
    detail: Optional[Union[str, List[str]]] = Field(default=None, description="Detailed analysis (Markdown string or list of bullet points)")
    citations: list[str] = Field(default=[], description="List of citation markers like [N1], [F2], [D3]")
    sources: list[str] = Field(default=[], description="List of source names used")
    highlights: list[str] = Field(default=[], description="List of 3-5 short key highlights/metrics")


class FinancialTopic(BaseModel):
    score: int = Field(description="Score out of 100")
    summary: Optional[str] = Field(default="No summary available", description="Summary of performance in this area")
    detail: Optional[Union[str, List[str]]] = Field(default=None, description="Detailed analysis (Markdown string or list of bullet points)")
    citations: list[str] = Field(default=[], description="List of citation markers like [N1], [F2], [D3]")
    sources: list[str] = Field(default=[], description="List of source names used")
    highlights: list[str] = Field(default=[], description="List of 3-5 short key highlights/metrics")


class ESGAnalysisOutput(BaseModel):
    overview: ESGTopic = Field(default_factory=lambda: ESGTopic(score=0, summary="Data Not Available"))
    governance: ESGTopic = Field(default_factory=lambda: ESGTopic(score=0, summary="Data Not Available"))
    environmental: ESGTopic = Field(default_factory=lambda: ESGTopic(score=0, summary="Data Not Available"))
    social: ESGTopic = Field(default_factory=lambda: ESGTopic(score=0, summary="Data Not Available"))
    disclosure: ESGTopic = Field(default_factory=lambda: ESGTopic(score=0, summary="Data Not Available"))


class FinancialAnalysisOutput(BaseModel):
    valuation: FinancialTopic = Field(default_factory=lambda: FinancialTopic(score=0, summary="Data Not Available"))
    profitability: FinancialTopic = Field(default_factory=lambda: FinancialTopic(score=0, summary="Data Not Available"))
    growth: FinancialTopic = Field(default_factory=lambda: FinancialTopic(score=0, summary="Data Not Available"))
    health: FinancialTopic = Field(default_factory=lambda: FinancialTopic(score=0, summary="Data Not Available"))


class DebateSynthesis(BaseModel):
    """FEATURE 3: Synthesis of structured debate"""
    bull_arguments: List[str] = Field(default=[], description="Key bull arguments from all agents")
    bear_arguments: List[str] = Field(default=[], description="Key bear arguments from all agents")
    evidence_clashes: List[str] = Field(default=[], description="Where data conflicts")
    winner: str = Field(default="undecided", description="'bull', 'bear', or 'undecided'")
    reasoning: str = Field(default="", description="Why this side won the debate")


class InvestmentDecision(BaseModel):
    rating: str = Field(description="Investment rating: BUY, SELL, or HOLD")
    confidence_score: int = Field(description="Confidence score between 0 and 100")
    summary: str = Field(description="Executive summary of the investment thesis (Markdown)")
    bull_case: str = Field(description="Key arguments for the bull case (Markdown)")
    bear_case: str = Field(description="Key arguments for the bear case (Markdown)")
    risk_factors: str = Field(description="Major risk factors identified (Markdown)")
    esg_analysis: ESGAnalysisOutput = Field(description="Detailed ESG Breakdown")
    financial_analysis: FinancialAnalysisOutput = Field(description="Detailed Financial Breakdown")
    # FEATURE 3: Debate synthesis
    debate_synthesis: Optional[DebateSynthesis] = Field(default=None, description="Synthesis of bull vs bear debate")
    # FEATURE 4: Verdict for Flip Card
    verdict: Optional[Verdict] = Field(default=None, description="Flip card verdict")


def normalize_detail(topic: Any):
    """Helper to convert list detail to string, force sources, and clean highlights"""
    if topic:
        if topic.detail and isinstance(topic.detail, list):
            # Force bullet point formatting, handling existing markers
            cleaned_details = []
            for d in topic.detail:
                s = str(d).strip()
                # Strip existing markers
                while s.startswith(('-', '*', '•')):
                    s = s[1:].strip()
                cleaned_details.append(f"- {s}")
            topic.detail = "\n".join(cleaned_details)

        elif topic.detail and isinstance(topic.detail, str):
            # If string, try to ensure it's not just a big block
            s = topic.detail.strip()
            # If it looks like a paragraph (no newlines), we might want to split sentences?
            # For now, just leave it, but prompt checks should handle this.
            pass

        if topic.highlights and isinstance(topic.highlights, list):
            topic.highlights = [str(h).replace("**", "").replace("*", "").strip() for h in topic.highlights]
    return topic


def get_role_focus_prompt(user_role: str) -> str:
    """FEATURE 5: Generate role-specific focus instructions for polymorphic analysis"""
    if user_role == "credit_risk":
        return """
CRITICAL - CREDIT RISK STAKEHOLDER FOCUS:
You are analyzing for a Credit Risk professional. Prioritize:
1. DEBT RATIOS: Debt-to-Equity, Interest Coverage, Debt Service Coverage
2. CASH FLOW STABILITY: Operating cash flow trends, free cash flow
3. BANKRUPTCY RISK INDICATORS: Altman Z-Score considerations, liquidity ratios
4. COVENANT COMPLIANCE: Any debt covenant concerns
5. COUNTERPARTY RISK: Customer concentration, supplier dependencies

Weight financial health (40%) and debt metrics higher than growth.
De-prioritize stock price and market sentiment.
"""
    elif user_role == "relationship_manager":
        return """
CRITICAL - RELATIONSHIP MANAGER FOCUS:
You are analyzing for a Relationship Manager. Prioritize:
1. TALKING POINTS: Recent wins, announcements, milestones
2. NEWS HIGHLIGHTS: Key recent events for client conversations
3. RELATIONSHIP OPPORTUNITIES: New products, services, or needs
4. ESG STORY: Sustainability initiatives for values-based discussions
5. RISK ALERTS: Issues to be aware of before client meetings

Weight sentiment and news (35%) higher than detailed financial ratios.
Focus on actionable conversation starters.
"""
    else:  # Default: investor
        return """
INVESTOR FOCUS:
You are analyzing for an Investor. Prioritize:
1. GROWTH POTENTIAL: Revenue growth, market expansion
2. VALUATION: PE, PB, fair value assessment
3. MARKET SENTIMENT: Stock performance, analyst views
4. PROFITABILITY TRENDS: Margin expansion/compression
5. ESG RISKS: Material sustainability risks

Balance growth (30%) and profitability (25%) with other factors.
"""


def calculate_weighted_score(financial_analysis: FinancialAnalysisOutput,
                            esg_analysis: ESGAnalysisOutput,
                            weights: RoleWeights) -> int:
    """FEATURE 5: Calculate confidence score using role-based weights"""
    # Extract scores
    growth_score = financial_analysis.growth.score if financial_analysis.growth else 50
    profit_score = financial_analysis.profitability.score if financial_analysis.profitability else 50
    health_score = financial_analysis.health.score if financial_analysis.health else 50
    esg_score = esg_analysis.overview.score if esg_analysis.overview else 50

    # Weighted average (sentiment weight applied to ESG as proxy)
    weighted = (
        growth_score * weights.growth +
        profit_score * weights.profitability +
        health_score * weights.debt_health +
        esg_score * (weights.esg + weights.sentiment)
    )

    return min(100, max(0, int(weighted)))


# ============================================================
# FEATURE 2: Evaluate Sufficiency for Judge-Loop
# ============================================================

def evaluate_sufficiency(state: AgentState) -> Dict[str, Any]:
    """
    FEATURE 2: Judge evaluates if the collected evidence is sufficient.
    Returns decision on whether to proceed or loop back for more research.
    """
    print(f"Judge: Evaluating evidence sufficiency for {state['company_name']}")

    news_analysis = state.get('news_analysis', '')
    financial_analysis = state.get('financial_analysis', '')
    claims_analysis = state.get('claims_analysis', '')

    # Get debate outputs
    news_debate = state.get('news_debate', {})
    financial_debate = state.get('financial_debate', {})
    claims_debate = state.get('claims_debate', {})

    # Check for obvious gaps
    has_news = bool(news_analysis and len(news_analysis) > 50)
    has_financial = bool(financial_analysis and len(financial_analysis) > 50)
    has_claims = bool(claims_analysis and len(claims_analysis) > 50)

    # Check for evidence clashes that need resolution
    all_clashes = []
    for debate in [news_debate, financial_debate, claims_debate]:
        if isinstance(debate, dict):
            clashes = debate.get('evidence_clash', [])
            if clashes:
                all_clashes.extend(clashes)

    # Quick heuristic evaluation (to save tokens)
    # Only call LLM for complex decisions
    if not has_news and not has_financial and not has_claims:
        return {
            'decision': 'sufficient',  # No data to loop on
            'loopback_instruction': None
        }

    # If all sources present and no major clashes, proceed
    if has_news and has_financial and has_claims and len(all_clashes) < 3:
        return {
            'decision': 'sufficient',
            'loopback_instruction': None
        }

    # If significant clashes or missing data, evaluate with LLM
    # Truncate inputs for token limits
    context = f"""
NEWS ({len(news_analysis)} chars): {"Present" if has_news else "MISSING"}
FINANCIAL ({len(financial_analysis)} chars): {"Present" if has_financial else "MISSING"}
DOCUMENTS ({len(claims_analysis)} chars): {"Present" if has_claims else "MISSING"}

Evidence Clashes Detected: {len(all_clashes)}
{chr(10).join([str(c) for c in all_clashes[:5]]) if all_clashes else "None"}
"""

    prompt = f"""You are evaluating if evidence is sufficient to make an investment verdict.

{context}

DECISION OPTIONS:
1. "sufficient" - Proceed to verdict (enough data, clashes can be resolved)
2. "needs_news" - Need more news research (specify what)
3. "needs_financial" - Need more financial data (specify what)
4. "needs_claims" - Need more document analysis (specify what)

Respond in JSON format:
{{
    "decision": "sufficient|needs_news|needs_financial|needs_claims",
    "research_query": "Specific query for loopback if not sufficient",
    "reasoning": "Brief explanation"
}}

Prefer "sufficient" unless there's a critical gap. Be decisive."""

    try:
        llm = get_llm("llama-3.1-8b-instant")
        response = llm.invoke([
            SystemMessage(content="You are a decisive judge. Output only valid JSON."),
            HumanMessage(content=prompt)
        ])

        result = json.loads(response.content)
        decision = result.get('decision', 'sufficient')

        if decision != 'sufficient':
            return {
                'decision': decision,
                'loopback_instruction': {
                    'target_agent': decision.replace('needs_', ''),
                    'research_query': result.get('research_query', ''),
                    'context': result.get('reasoning', '')
                }
            }

        return {'decision': 'sufficient', 'loopback_instruction': None}

    except Exception as e:
        print(f"Sufficiency evaluation error: {e}, proceeding to verdict")
        return {'decision': 'sufficient', 'loopback_instruction': None}


# ============================================================
# Main Judge Agent
# ============================================================

def judge_agent(state: AgentState) -> Dict[str, Any]:
    """
    Synthesizes all analyses and generates a final report.
    FEATURE 3: Synthesizes structured debate (Bull vs Bear)
    FEATURE 4: Outputs Flip Card verdict format
    FEATURE 5: Applies polymorphic analysis based on user_role
    """
    print(f"Judge Agent: deliberating for {state['company_name']}")

    # FEATURE 5: Get user role for polymorphic analysis
    user_role = state.get('user_role', 'investor')
    role_focus = get_role_focus_prompt(user_role)

    try:
        role_enum = AnalysisPersona(user_role)
        weights = get_role_weights(role_enum)
    except:
        weights = RoleWeights()

    # Get debate outputs for synthesis
    news_debate = state.get('news_debate', {})
    financial_debate = state.get('financial_debate', {})
    claims_debate = state.get('claims_debate', {})

    # Collect all bull/bear arguments
    all_bull = []
    all_bear = []
    all_clashes = []

    for debate in [news_debate, financial_debate, claims_debate]:
        if isinstance(debate, dict):
            bull = debate.get('bull_argument', {})
            bear = debate.get('bear_argument', {})
            if isinstance(bull, dict) and bull.get('claim'):
                all_bull.append(bull['claim'])
            if isinstance(bear, dict) and bear.get('claim'):
                all_bear.append(bear['claim'])
            clashes = debate.get('evidence_clash', [])
            if clashes:
                all_clashes.extend(clashes)

    # Truncate analyses for token limits
    news_analysis = state.get('news_analysis', 'No data')[:3000]
    financial_analysis = state.get('financial_analysis', 'No data')[:3000]
    claims_analysis = state.get('claims_analysis', 'No data')[:3000]

    # Get sources for citation reference
    sources = state.get('sources', [])
    sources_summary = "\n".join([
        f"- [{s.get('id', '?')}] {s.get('title', 'Unknown')} ({s.get('type', 'unknown')})"
        for s in sources[:15]  # Limit to 15 sources
    ]) if sources else "No sources registered"

    prompt = f"""You are a Chief Investment Officer (Judge) for {state['company_name']}.

{role_focus}

=== AVAILABLE SOURCES (use these citation IDs) ===
{sources_summary}

=== ANALYSES ===
1. NEWS ANALYSIS:
{news_analysis}

2. FINANCIAL ANALYSIS:
{financial_analysis}

3. CLAIMS/DOCUMENTS ANALYSIS:
{claims_analysis}

=== STRUCTURED DEBATE RESULTS ===
BULL ARGUMENTS:
{chr(10).join(f"- {a}" for a in all_bull) if all_bull else "None provided"}

BEAR ARGUMENTS:
{chr(10).join(f"- {a}" for a in all_bear) if all_bear else "None provided"}

EVIDENCE CLASHES:
{chr(10).join(f"- {c}" for c in all_clashes[:5]) if all_clashes else "None detected"}

=== INSTRUCTIONS ===
1. Synthesize findings into a cohesive investment report
2. Resolve conflicts between bull and bear arguments
3. Declare which side (bull/bear) WON the debate and WHY
4. Assign Rating (BUY/SELL/HOLD) and Confidence Score (0-100)

=== FEATURE 4: VERDICT FOR FLIP CARD UI ===
You MUST include a "verdict" object with:
- "action": "BUY", "SELL", or "HOLD"
- "headline_reasoning": A SHORT punchy sentence (max 100 chars) for card front
- "deep_dive_justification": Detailed paragraph for card back citing winning arguments
- "winning_debate_side": "bull" or "bear"
- "key_citations": List of citation IDs used (e.g., ["[N1]", "[F2]"])

=== ESG & FINANCIAL ANALYSIS ===
Provide detailed breakdowns with:
- Scores (0-100)
- Summaries: **4-5 sentences** adhering to the following:
  - **Bold** key financial/ESG terms and metrics.
  - Focus on material facts.
- **Detail**:
  - **MANDATORY**: Separate from Summary.
  - Format as **bullet points** (Markdown list).
  - **Bold** key metrics/findings.
  - Cite specific evidence.
  - Length: 3-4 bullet points minimum.
- Highlights: 3-5 SPECIFIC data points (PLAIN TEXT)
- Citations using [N1], [F2], [D3] format in BOTH text and the 'citations' field.

=== CITATION RULES ===
[N*] = News sources
[F*] = Financial statements
[D*] = Documents

CRITICAL: Every claim needs a citation. Populate ALL fields, especially 'detail'."""

    llm = get_llm("llama-3.3-70b-versatile")
    structured_llm = llm.with_structured_output(InvestmentDecision)

    try:
        print(f"Judge Agent: invoking LLM with {LLM_TIMEOUT}s timeout...")
        start_time = time.time()
        response = invoke_with_timeout(
            structured_llm,
            [
                SystemMessage(content=f"You are a decisive CIO analyzing for a {user_role.replace('_', ' ').title()}."),
                HumanMessage(content=prompt)
            ],
            LLM_TIMEOUT
        )
        print(f"Judge Agent: LLM completed in {time.time() - start_time:.2f}s")

        # Normalize fields
        if response.esg_analysis:
            for field in ['overview', 'governance', 'environmental', 'social', 'disclosure']:
                topic = getattr(response.esg_analysis, field)
                normalize_detail(topic)

        if response.financial_analysis:
            for field in ['valuation', 'profitability', 'growth', 'health']:
                topic = getattr(response.financial_analysis, field)
                normalize_detail(topic)

        # FEATURE 5: Apply role-based weighted scoring
        adjusted_score = calculate_weighted_score(
            response.financial_analysis,
            response.esg_analysis,
            weights
        )

        # Blend LLM confidence with weighted calculation
        final_confidence = int((response.confidence_score + adjusted_score) / 2)
        response.confidence_score = final_confidence

        # Ensure verdict is populated
        if not response.verdict:
            response.verdict = Verdict(
                action=VerdictAction(response.rating),
                headline_reasoning=response.summary[:100] if response.summary else "Analysis complete",
                deep_dive_justification=response.summary or "See detailed report",
                winning_debate_side="undecided",
                key_citations=[]
            )

        # Save to DB
        with Session(engine) as session:
            report = AnalysisReport(
                company_id=state['company_id'],
                rating=response.rating,
                confidence_score=response.confidence_score,
                summary=response.summary,
                bull_case=response.bull_case,
                bear_case=response.bear_case,
                risk_factors=response.risk_factors,
                esg_analysis=response.esg_analysis.model_dump(),
                financial_analysis=response.financial_analysis.model_dump(),
                agent_logs=[
                    {"agent": "news", "output": state.get('news_analysis')},
                    {"agent": "financial", "output": state.get('financial_analysis')},
                    {"agent": "claims", "output": state.get('claims_analysis')},
                    {"agent": "debate", "bull": all_bull, "bear": all_bear, "clashes": all_clashes},
                    {"agent": "verdict", "output": response.verdict.model_dump() if response.verdict else None},
                    {"agent": "sources", "output": sources},
                    {"agent": "user_role", "output": user_role}
                ]
            )
            session.add(report)
            session.commit()
            session.refresh(report)
            print(f"Report saved with ID: {report.id}")

            # Embed Report for Vector Search
            try:
                print("Generating embeddings for report chunks...")
                rag_service = RAGService()
                chunks_to_add = []

                sections = [
                    ("summary", f"**Investment Thesis**:\n{response.summary}"),
                    ("bull_case", f"**Bull Case**:\n{response.bull_case}"),
                    ("bear_case", f"**Bear Case**:\n{response.bear_case}"),
                    ("risk_factors", f"**Risk Factors**:\n{response.risk_factors}")
                ]

                for idx, (section_type, content) in enumerate(sections):
                    if not content or len(content) < 10:
                        continue

                    context_content = f"[{state['company_name']} Analysis Report - {section_type.replace('_', ' ').title()}]\n{content}"
                    embedding = rag_service.embed_query(context_content)

                    if embedding:
                        chunk = ReportChunk(
                            report_id=report.id,
                            content=context_content,
                            chunk_index=idx,
                            section_type=section_type,
                            embedding=embedding
                        )
                        chunks_to_add.append(chunk)

                if chunks_to_add:
                    session.add_all(chunks_to_add)
                    session.commit()
                    print(f"Saved {len(chunks_to_add)} report vector chunks.")

            except Exception as e:
                print(f"Error embedding report chunks: {e}")

        return {
            "final_report": response.summary,
            "verdict": response.verdict.model_dump() if response.verdict else None,
            "sources": sources
        }

    except LLMTimeoutError as e:
        print(f"Judge Agent TIMEOUT: {e}")
        import traceback
        traceback.print_exc()

    except Exception as e:
        import traceback
        print(f"Error in Judge Agent: {e}")
        traceback.print_exc()
        if hasattr(e, 'errors'):
            print(f"Validation Errors: {e.errors()}")

        # Fallback mock response
        print("Using Mock Judge Response for Verification")

        mock_verdict = Verdict(
            action=VerdictAction.HOLD,
            headline_reasoning="Analysis encountered an error - manual review recommended",
            deep_dive_justification="The automated analysis encountered an error. Please review the underlying data manually.",
            winning_debate_side="undecided",
            key_citations=[]
        )

        mock_esg_topic = ESGTopic(
            score=50,
            summary="Data unavailable, using fallback estimation.",
            citations=["[1]"],
            sources=["System Fallback"]
        )

        mock_decision = InvestmentDecision(
            rating="HOLD",
            confidence_score=50,
            summary="**Fallback Report**: The Judge Agent encountered an error. Manual review recommended.",
            bull_case="- Unable to complete automated analysis",
            bear_case="- System error occurred during processing",
            risk_factors="- Automated analysis incomplete",
            esg_analysis=ESGAnalysisOutput(
                overview=mock_esg_topic,
                governance=mock_esg_topic,
                environmental=mock_esg_topic,
                social=mock_esg_topic,
                disclosure=mock_esg_topic
            ),
            financial_analysis=FinancialAnalysisOutput(
                valuation=FinancialTopic(score=50, summary="N/A", citations=[], sources=[]),
                profitability=FinancialTopic(score=50, summary="N/A", citations=[], sources=[]),
                growth=FinancialTopic(score=50, summary="N/A", citations=[], sources=[]),
                health=FinancialTopic(score=50, summary="N/A", citations=[], sources=[])
            ),
            verdict=mock_verdict
        )

        with Session(engine) as session:
            report = AnalysisReport(
                company_id=state['company_id'],
                rating=mock_decision.rating,
                confidence_score=mock_decision.confidence_score,
                summary=mock_decision.summary,
                bull_case=mock_decision.bull_case,
                bear_case=mock_decision.bear_case,
                risk_factors=mock_decision.risk_factors,
                esg_analysis=mock_decision.esg_analysis.model_dump(),
                financial_analysis=mock_decision.financial_analysis.model_dump(),
                agent_logs=[
                    {"agent": "news", "output": state.get('news_analysis')},
                    {"agent": "financial", "output": state.get('financial_analysis')},
                    {"agent": "claims", "output": state.get('claims_analysis')},
                    {"agent": "error", "output": str(e)}
                ]
            )
            session.add(report)
            session.commit()
            session.refresh(report)
            print(f"Mock Report saved with ID: {report.id}")

            # Embed mock report
            try:
                rag_service = RAGService()
                mock_sections = [
                    ("summary", mock_decision.summary),
                    ("bull_case", mock_decision.bull_case),
                    ("bear_case", mock_decision.bear_case),
                    ("risk_factors", mock_decision.risk_factors)
                ]
                chunks = []
                for i, (stype, txt) in enumerate(mock_sections):
                    emb = rag_service.embed_query(f"{stype}: {txt}")
                    chunks.append(ReportChunk(report_id=report.id, content=txt, chunk_index=i, section_type=stype, embedding=emb))
                session.add_all(chunks)
                session.commit()
            except Exception as e:
                print(f"Error embedding mock chunks: {e}")

            return {
                "final_report": mock_decision.summary,
                "verdict": mock_verdict.model_dump(),
                "errors": [str(e)]
            }
