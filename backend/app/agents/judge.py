"""
Judge Agent - The CIO (Chief Investment Officer)

Synthesizes all agent analyses into a final decision based on user's role.
Implements:
1. Citation preservation and hallucination checking
2. Role-specific evaluation logic
3. Structured FinalAnalysisOutput generation
4. Debate report synthesis
"""

from typing import Dict, Any, Optional, Union, List
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session
from datetime import datetime, timezone
from app.database import engine
from app.models import AnalysisReport, ReportChunk
from app.services.rag import RAGService
from app.agents.base import get_llm
from app.agents.state import AgentState
from app.agents.persona_config import get_persona_config
from app.agents.prompts import get_judge_prompt, ROLE_INSTRUCTIONS
from app.agents.citation_models import (
    FinalAnalysisOutput,
    RoleBasedInsight,
    ESGReport,
    FinancialReport,
    MarketSentiment,
    DebateReport,
    DebateStance,
    SectionContent,
    SourceMetadata,
    validate_citations,
    extract_citations_from_text
)
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from app.services.content_optimizer import content_optimizer

import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from langchain_core.messages import SystemMessage, HumanMessage

# Timeout configuration (in seconds)
LLM_TIMEOUT = 300  # 5 minutes for Judge Agent LLM call

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

def clean_and_parse_json(text: str, parser: JsonOutputParser) -> "JudgeDecisionOutput":
    """
    Clean the raw LLM output (fix brackets, remove markdown) and parse it.
    """
    # 1. Remove Markdown code blocks ```json ... ```
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    
    # 2. Fix Double Brackets [[D1]] -> [D1] or [[D1], Page 123] -> [D1], Page 123
    # This handles LLM quirks where it wraps citations in extra brackets
    text = re.sub(r'\[{2,}([NFD]\d+.*?\]*)\s*\]{2,}', r'[\1]', text)
    
    # 3. Parse
    try:
        return parser.parse(text)
    except OutputParserException:
        # Try to find the JSON object boundaries if there's extra text
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                return parser.parse(json_str)
        except:
            pass
        raise



# =============================================================================
# STRUCTURED OUTPUT MODELS FOR JUDGE
# =============================================================================

class JudgeSectionOutput(BaseModel):
    """Section output for ESG/Financial analysis."""
    preview_summary: str = Field(default="Data not available for analysis.", description="Comprehensive 3-5 sentence summary with key findings and their implications")
    detailed_findings: List[str] = Field(default_factory=list, description="5-8 bullet points with citations [N#], [F#], [D#]. Use **bold** for important metrics and terms.")
    confidence_score: int = Field(default=50, ge=0, le=100)
    highlights: List[str] = Field(default_factory=list, description="3-5 key metrics or data points")


class JudgeESGOutput(BaseModel):
    """ESG analysis structured output."""
    overview: JudgeSectionOutput = Field(default_factory=JudgeSectionOutput)
    governance: JudgeSectionOutput = Field(default_factory=JudgeSectionOutput)
    environmental: JudgeSectionOutput = Field(default_factory=JudgeSectionOutput)
    social: JudgeSectionOutput = Field(default_factory=JudgeSectionOutput)
    disclosure: JudgeSectionOutput = Field(default_factory=JudgeSectionOutput)


class JudgeFinancialOutput(BaseModel):
    """Financial analysis structured output."""
    valuation: JudgeSectionOutput = Field(default_factory=JudgeSectionOutput)
    profitability: JudgeSectionOutput = Field(default_factory=JudgeSectionOutput)
    growth: JudgeSectionOutput = Field(default_factory=JudgeSectionOutput)
    health: JudgeSectionOutput = Field(default_factory=JudgeSectionOutput)


class JudgeMarketSentimentOutput(BaseModel):
    """Market sentiment from news analysis."""
    sentiment: str = Field(default="NEUTRAL", description="POSITIVE | NEUTRAL | NEGATIVE")
    summary: str = Field(default="No recent news available.", description="2-3 sentences on market perception with [N#] citations")
    key_events: List[str] = Field(default_factory=list, description="3-5 recent events affecting the company [N#]")
    risks_from_news: List[str] = Field(default_factory=list, description="2-3 news-based risks or concerns [N#]")


class JudgeDebateOutput(BaseModel):
    """Debate report structured output."""
    government_summary: str = Field(default="Pro stance pending.")
    government_arguments: List[str] = Field(default_factory=list)
    opposition_summary: str = Field(default="Skeptic stance pending.")
    opposition_arguments: List[str] = Field(default_factory=list)
    verdict: str = Field(default="Verdict pending.")
    # New optional fields for enhanced verdict display
    verdict_reasoning: str = Field(default="", description="2-3 sentence explanation of why this verdict was reached")
    verdict_key_factors: List[str] = Field(default_factory=list, description="3-5 key factors with citations that influenced the verdict")
    transcript: str = Field(default="", description="Full markdown transcript of the debate")


class JudgeDecisionOutput(BaseModel):
    """Complete Judge output structure."""
    decision: str = Field(..., description="Role-specific decision (BUY/SELL/HOLD, etc.)")
    confidence_score: int = Field(default=50, ge=0, le=100)
    confidence_reasoning: str = Field(..., description="Explanation for the confidence score (e.g., 'Data is comprehensive', 'Missing Scope 3 data')")
    justification: str = Field(..., description="Why this decision, with citations")
    key_concerns: List[str] = Field(default_factory=list, description="Top concerns with citations")
    summary: str = Field(..., description="Executive summary")
    bull_case: str = Field(..., description="Bull case arguments")
    bear_case: str = Field(..., description="Bear case arguments")
    risk_factors: str = Field(..., description="Key risks")
    market_sentiment: JudgeMarketSentimentOutput = Field(default_factory=JudgeMarketSentimentOutput)
    esg_analysis: JudgeESGOutput = Field(default_factory=JudgeESGOutput)
    financial_analysis: JudgeFinancialOutput = Field(default_factory=JudgeFinancialOutput)
    debate: JudgeDebateOutput = Field(default_factory=JudgeDebateOutput)
    analysis_focus_area: str = Field(default="Overview", description="Focus area for the analysis")

    # Removed complex validator for stability
    # @field_validator('analysis_focus_area', mode='before') ...


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def validate_report_quality(
    judge_output: JudgeDecisionOutput,
    citation_registry: Dict[str, Any],
    state: AgentState
) -> Dict[str, Any]:
    """
    Validate the report quality and identify areas that need improvement.

    Returns:
        Dict with validation_passed (bool), issues (list), and recommendations (list)
    """
    issues = []
    recommendations = []

    # 1. Check if decision is made
    if not judge_output.decision or judge_output.decision == "PENDING":
        issues.append("No clear decision was made")
        recommendations.append("Re-run analysis with more data")

    # 2. Check confidence score
    if judge_output.confidence_score < 30:
        issues.append(f"Very low confidence score ({judge_output.confidence_score}%)")
        recommendations.append("Consider gathering more data sources")

    # 3. Check key concerns
    if not judge_output.key_concerns or len(judge_output.key_concerns) < 2:
        issues.append("Insufficient key concerns identified")
        recommendations.append("Review risk analysis more thoroughly")

    # 4. Check ESG sections for substance
    esg_sections = ['overview', 'governance', 'environmental', 'social', 'disclosure']
    empty_esg_sections = []
    for section_name in esg_sections:
        section = getattr(judge_output.esg_analysis, section_name, None)
        if section:
            if not section.detailed_findings or len(section.detailed_findings) < 2:
                empty_esg_sections.append(section_name)
            if section.preview_summary and len(section.preview_summary) < 50:
                issues.append(f"ESG {section_name} summary too short")

    if empty_esg_sections:
        issues.append(f"Missing detailed findings in ESG sections: {', '.join(empty_esg_sections)}")
        recommendations.append("Claims Agent may need more document data")

    # 5. Check Financial sections for substance
    financial_sections = ['valuation', 'profitability', 'growth', 'health']
    empty_financial_sections = []
    for section_name in financial_sections:
        section = getattr(judge_output.financial_analysis, section_name, None)
        if section:
            if not section.detailed_findings or len(section.detailed_findings) < 2:
                empty_financial_sections.append(section_name)
            if section.preview_summary and len(section.preview_summary) < 50:
                issues.append(f"Financial {section_name} summary too short")

    if empty_financial_sections:
        issues.append(f"Missing detailed findings in Financial sections: {', '.join(empty_financial_sections)}")
        recommendations.append("Financial Agent may need more data")

    # 6. Check debate section
    if not judge_output.debate.government_arguments or len(judge_output.debate.government_arguments) < 2:
        issues.append("Insufficient bullish arguments in debate")
    if not judge_output.debate.opposition_arguments or len(judge_output.debate.opposition_arguments) < 2:
        issues.append("Insufficient bearish arguments in debate")

    # 7. Check citation coverage
    news_citations = [k for k in citation_registry.keys() if k.startswith('N')]
    financial_citations = [k for k in citation_registry.keys() if k.startswith('F')]
    document_citations = [k for k in citation_registry.keys() if k.startswith('D')]

    if not news_citations:
        issues.append("No news citations [N#] found")
        recommendations.append("News Agent didn't find relevant articles")
    if not financial_citations:
        issues.append("No financial citations [F#] found")
        recommendations.append("Financial Agent didn't extract data")
    if not document_citations:
        issues.append("No document citations [D#] found")
        recommendations.append("Claims Agent didn't find relevant documents")

    validation_passed = len(issues) == 0

    # Log validation results
    if issues:
        print(f"Report Validation: {len(issues)} issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print("Recommendations:")
        for rec in recommendations:
            print(f"  - {rec}")
    else:
        print("Report Validation: PASSED - All quality checks passed")

    return {
        "validation_passed": validation_passed,
        "issues": issues,
        "recommendations": recommendations,
        "citation_coverage": {
            "news": len(news_citations),
            "financial": len(financial_citations),
            "document": len(document_citations)
        }
    }


def check_citation_hallucinations(text: str, citation_registry: Dict[str, Any]) -> List[str]:
    """
    Check for hallucinated citations - IDs in text that don't exist in registry.

    Args:
        text: Text containing citation IDs
        citation_registry: The global citation registry

    Returns:
        List of hallucinated citation IDs
    """
    # Match patterns like [N1], [F2], [D3]
    citation_pattern = r'\[([NFD]\d+)\]'
    found_citations = set(re.findall(citation_pattern, text))

    hallucinated = []
    for citation_id in found_citations:
        if citation_id not in citation_registry:
            hallucinated.append(citation_id)

    return hallucinated


def convert_section_to_content(section: JudgeSectionOutput) -> SectionContent:
    """Convert JudgeSectionOutput to SectionContent for final output."""
    return SectionContent(
        preview_summary=section.preview_summary,
        detailed_findings=section.detailed_findings,
        confidence_score=section.confidence_score,
        highlights=section.highlights
    )


def build_final_output(
    state: AgentState,
    judge_output: JudgeDecisionOutput,
    citation_registry: Dict[str, Any]
) -> FinalAnalysisOutput:
    """Build the complete FinalAnalysisOutput from Judge output."""

    # Convert ESG sections
    esg_report = ESGReport(
        overview=convert_section_to_content(judge_output.esg_analysis.overview),
        governance_integration=convert_section_to_content(judge_output.esg_analysis.governance),
        environmental=convert_section_to_content(judge_output.esg_analysis.environmental),
        social=convert_section_to_content(judge_output.esg_analysis.social),
        disclosure_quality=convert_section_to_content(judge_output.esg_analysis.disclosure)
    )

    # Convert Financial sections
    financial_report = FinancialReport(
        valuation=convert_section_to_content(judge_output.financial_analysis.valuation),
        profitability=convert_section_to_content(judge_output.financial_analysis.profitability),
        growth=convert_section_to_content(judge_output.financial_analysis.growth),
        financial_health=convert_section_to_content(judge_output.financial_analysis.health)
    )

    # Build Market Sentiment (from news analysis)
    market_sentiment = MarketSentiment(
        sentiment=judge_output.market_sentiment.sentiment,
        summary=judge_output.market_sentiment.summary,
        key_events=judge_output.market_sentiment.key_events,
        risks_from_news=judge_output.market_sentiment.risks_from_news
    )

    # Build Debate Report
    # Extract debate transcript from state (bypass LLM copying which often fails)
    debate_transcript_list = state.get('debate_transcript', []) or []
    actual_transcript = "\n\n".join(debate_transcript_list) if debate_transcript_list else ""
    
    debate_report = DebateReport(
        government_stand=DebateStance(
            stance_summary=judge_output.debate.government_summary,
            arguments=judge_output.debate.government_arguments
        ),
        opposition_stand=DebateStance(
            stance_summary=judge_output.debate.opposition_summary,
            arguments=judge_output.debate.opposition_arguments
        ),
        judge_verdict=judge_output.debate.verdict,
        verdict_reasoning=judge_output.debate.verdict_reasoning,
        verdict_key_factors=judge_output.debate.verdict_key_factors,
        transcript=actual_transcript  # Use actual transcript from state, not LLM output
    )

    # Build Role-Based Insight
    role_report = RoleBasedInsight(
        user_role=state.get('analysis_persona', 'INVESTOR'),
        decision=judge_output.decision,
        justification=judge_output.justification,
        key_concerns=judge_output.key_concerns,
        confidence_score=judge_output.confidence_score
    )

    # Convert citation_registry to SourceMetadata objects
    typed_registry = {}
    for cid, meta in citation_registry.items():
        if isinstance(meta, dict):
            typed_registry[cid] = SourceMetadata(
                id=meta.get('id', cid),
                title=meta.get('title', 'Unknown'),
                url_or_path=meta.get('url_or_path', ''),
                type=meta.get('type', 'Document'),
                date=meta.get('date'),
                page_number=meta.get('page_number'),
                row_line=meta.get('row_line')
            )

    # Build final output
    return FinalAnalysisOutput(
        company_name=state['company_name'],
        company_id=state['company_id'],
        analysis_timestamp=datetime.now(timezone.utc).isoformat(),
        role_report=role_report,
        esg_report=esg_report,
        financial_report=financial_report,
        market_sentiment=market_sentiment,
        debate_report=debate_report,
        citation_registry=typed_registry,
        # Legacy compatibility
        rating=judge_output.decision,
        confidence_score=judge_output.confidence_score,
        summary=judge_output.summary,
        bull_case=judge_output.bull_case,
        bear_case=judge_output.bear_case,
        risk_factors=judge_output.risk_factors
    )


def save_report_to_db(
    state: AgentState,
    final_output: FinalAnalysisOutput,
    judge_output: JudgeDecisionOutput
) -> Optional[str]:
    """Save the analysis report to database and return report ID."""
    try:
        with Session(engine) as session:
            report = AnalysisReport(
                company_id=state['company_id'],
                rating=judge_output.decision,
                confidence_score=judge_output.confidence_score,
                summary=judge_output.summary,
                
                # Role-Based Insights
                justification=f"**Confidence Reasoning:**\n{judge_output.confidence_reasoning}\n\n**{'Engagement Rationale' if state.get('analysis_persona') == 'RELATIONSHIP_MANAGER' else 'Investment Rationale'}:**\n{judge_output.justification}",
                key_concerns=judge_output.key_concerns,
                
                bull_case=judge_output.bull_case,
                bear_case=judge_output.bear_case,
                risk_factors=judge_output.risk_factors,
                esg_analysis=final_output.esg_report.model_dump(),
                financial_analysis=final_output.financial_report.model_dump(),
                analysis_persona=state.get('analysis_persona', 'INVESTOR'),
                analysis_focus_area={"focus": judge_output.analysis_focus_area},
                agent_logs=[
                    {"agent": "news", "output": state.get('news_analysis')},
                    {"agent": "financial", "output": state.get('financial_analysis')},
                    {"agent": "claims", "output": state.get('claims_analysis')},
                    {"agent": "critique", "output": {
                        "news_critique": state.get('news_critique'),
                        "financial_critique": state.get('financial_critique'),
                        "claims_critique": state.get('claims_critique')
                    }},
                    {"agent": "debate", "output": final_output.debate_report.model_dump()},
                    {"agent": "market_sentiment", "output": final_output.market_sentiment.model_dump()},
                    {"agent": "citation_registry", "output": {
                        k: v.model_dump() if hasattr(v, 'model_dump') else v
                        for k, v in final_output.citation_registry.items()
                    }}
                ]
            )
            session.add(report)
            session.commit()
            session.refresh(report)

            if not report.id:
                print("CRITICAL ERROR: Report ID is None after commit/refresh")
                return None

            print(f"Report saved with ID: {report.id}")

            # Embed report for vector search
            try:
                print("Generating embeddings for report chunks...")
                rag_service = RAGService()
                chunks_to_add = []

                sections = [
                    ("summary", f"**Investment Thesis**:\n{judge_output.summary}"),
                    ("bull_case", f"**Bull Case**:\n{judge_output.bull_case}"),
                    ("bear_case", f"**Bear Case**:\n{judge_output.bear_case}"),
                    ("risk_factors", f"**Risk Factors**:\n{judge_output.risk_factors}")
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

            return str(report.id)

    except Exception as e:
        print(f"Error saving report to DB: {e}")
        import traceback
        traceback.print_exc()
        return None


# =============================================================================
# MAIN JUDGE AGENT
# =============================================================================

def judge_agent(state: AgentState) -> Dict[str, Any]:
    """
    Synthesizes all analyses and generates a final report.

    Key Features:
    1. Role-specific decision framework
    2. Citation preservation and hallucination checking
    3. Structured FinalAnalysisOutput generation
    4. Debate synthesis

    Returns:
        Dict with final_report, final_output_json, and hallucinated_citations
    """
    persona = state.get('analysis_persona', 'INVESTOR')
    config = get_persona_config(persona)
    persona_label = persona.replace('_', ' ').title()
    company_name = state['company_name']

    print(f"Judge Agent: deliberating for {company_name} [Persona: {persona}]")

    # Get citation registry from state
    citation_registry = dict(state.get('citation_registry', {}))

    # Build decision context
    decision_options = " | ".join(config['decision_options'])

    # Get role-specific focus instructions
    role_specific_instructions = ROLE_INSTRUCTIONS.get(persona, ROLE_INSTRUCTIONS['INVESTOR'])

    # Build the comprehensive prompt
    # Use content optimizer for smart truncation (preserves key insights)
    news_an = state.get('news_analysis', 'No data')
    fin_an = state.get('financial_analysis', 'No data')
    claims_an = state.get('claims_analysis', 'No data')

    # Smart content optimization (Target < 6000 tokens total)
    # Allocation: News 25%, Financial 30%, Claims 45% (ESG critical)
    # Total budget ~9000 chars for analyses, leaving room for prompt template + output
    news_an, fin_an, claims_an = content_optimizer.optimize_for_judge(
        news_an, fin_an, claims_an,
        max_total_tokens=2800  # Increased to ~11k chars to capture more ESG detail
    )

    # Extract debate arguments and transcript
    gov_args = state.get('government_arguments', []) or []
    opp_args = state.get('opposition_arguments', []) or []
    debate_transcript_list = state.get('debate_transcript', []) or []
    debate_transcript_str = "\n\n".join(debate_transcript_list) if debate_transcript_list else "No debate conducted."
    
    # DEBUG: Log transcript info
    print(f"DEBUG: Debate transcript has {len(debate_transcript_list)} entries, {len(debate_transcript_str)} chars")
    if debate_transcript_list:
        print(f"DEBUG: First entry: {debate_transcript_list[0][:100]}...")
    
    # Financial/Gov defense is usually the 2nd item if present
    gov_defense = "No defense provided."
    if len(gov_args) > 1:
        gov_defense = gov_args[1]
        
    # News/Opp defense is usually the 2nd item if present
    opp_defense = "No defense provided."
    if len(opp_args) > 1:
        opp_defense = opp_args[1]
    # Format raw evidence for ground truth check
    raw_ev_dict = state.get('raw_evidence', {})
    raw_evidence_str = ""
    for category, points in raw_ev_dict.items():
        raw_evidence_str += f"### {category.upper()} EVIDENCE:\n"
        if points:
            for p in points:
                # Handle both object and dict (serialization safety)
                if isinstance(p, dict):
                    content = p.get('content', '')
                    citation = p.get('citation', '')
                elif hasattr(p, 'content'):
                    content = getattr(p, 'content', '')
                    citation = getattr(p, 'citation', '')
                else:
                    content = str(p)
                    citation = ""
                
                raw_evidence_str += f"- {content} {citation}\n"
        else:
            raw_evidence_str += "No structured evidence.\n"
        raw_evidence_str += "\n"

    prompt = get_judge_prompt(
        company_name=company_name,
        persona=persona,
        news_analysis=news_an,
        financial_analysis=fin_an,
        claims_analysis=claims_an,
        news_critique=state.get('news_critique', 'No critique')[:800],
        financial_critique=state.get('financial_critique', 'No critique')[:800],
        claims_critique=state.get('claims_critique', 'No critique')[:800],
        government_defense=gov_defense[:800],
        opposition_defense=opp_defense[:800],
        raw_evidence=raw_evidence_str[:4000],  # Limit size to avoid overflow
        debate_transcript=debate_transcript_str  # Pass actual debate transcript
    )

    # Setup Parser
    parser = JsonOutputParser(pydantic_object=JudgeDecisionOutput)
    format_instructions = parser.get_format_instructions()

    system_prompt = f"""You are a decisive, objective Chief Investment Officer acting as a {persona_label}.

CRITICAL RULES:
1. PRESERVE all citation IDs from sub-agents: [N#], [F#], [D#]
2. PRESERVE PAGE NUMBERS: If a citation includes a page number (e.g., [D1], Page 123), you MUST include it exactly.
3. NEVER strip or remove citation markers or their associated page numbers from your output.
4. USE ONLY PROVIDED SPECIFIC IDs (e.g., [N1], [D5]). DO NOT use generic placeholders like [N#], [D#], [F#]. If no specific ID is available, do not fake one.
5. CITATION FORMAT: Use SINGLE brackets like [D1] or [D1], Page 123. DO NOT use double brackets like [[D1]].
5. Every claim must reference original source citations
6. Generate structured JSON output following the exact schema.
7. KEEP IT CONCISE: Avoid excessively long prose. Summaries should be <200 words.
8. NO REPETITIVE CONTENT: Do not use the same generic claims (e.g., "Lack of transparency") across multiple sections. Each section must be unique.
9. NO GENERIC FALLBACKS: If data is missing for ESG/Governance/Social, state "Insufficient data" explicitly. 
10. STRICT SEPARATION: DO NOT use Financial data ([F#]) to fill gaps in Governance, Environmental, or Social sections. If no [D#] or [N#] citations exist for ESG, the section MUST be marked as "Data not available".
11. NO HALLUCINATION: Do not invent "stable financial reality" or similar phrases to mask missing data.

DECISION FRAMEWORK for {persona_label}:
- Decision Type: {config['decision_label']}
- Available Options: {decision_options}
- Primary Metric: {config['decision_metric']}

{role_specific_instructions}

Output valid JSON matching the schema below:
{format_instructions}
"""

    # === LLM CALL WITH FALLBACK ===
    try:
        # Attempt Primary: Cerebras
        try:
            llm = get_llm("llama-3.3-70b")
            print(f"Judge Agent: Attempting Cerebras (llama-3.3-70b)...")
            start_time = time.time()
            
            response_msg = invoke_with_timeout(
                llm,
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=prompt)
                ],
                LLM_TIMEOUT
            )
            print(f"Judge Agent: SUCCESS (Cerebras) in {time.time() - start_time:.2f}s")
        except Exception as e:
            print(f"Judge Agent: Cerebras failed: {e}. Fallback to Groq...")
            llm = get_llm("llama-3.1-8b-instant")
            start_time = time.time()
            response_msg = invoke_with_timeout(
                llm,
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=prompt)
                ],
                LLM_TIMEOUT
            )
            print(f"Judge Agent: SUCCESS (Groq) in {time.time() - start_time:.2f}s")

        # === PARSE OUTPUT (Common for both Cerebras & Groq success) ===
        response_text = response_msg.content
        response_data = clean_and_parse_json(response_text, parser)
        
        # Convert dict to Pydantic object if parser returns dict
        if isinstance(response_data, dict):
            response = JudgeDecisionOutput(**response_data)
        else:
            response = response_data

        # Build final output structure
        final_output = build_final_output(state, response, citation_registry)

        # Check for hallucinated citations
        all_text = " ".join([
            response.summary,
            response.bull_case,
            response.bear_case,
            response.risk_factors,
            response.justification,
            " ".join(response.key_concerns)
        ])

        hallucinated = check_citation_hallucinations(all_text, citation_registry)
        if hallucinated:
            print(f"WARNING: Found {len(hallucinated)} hallucinated citations: {hallucinated}")

        # Validate report quality
        validation_result = validate_report_quality(response, citation_registry, state)

        # Save to database
        report_id = save_report_to_db(state, final_output, response)

        return {
            "final_report": response.summary,
            "final_output_json": final_output.model_dump(),
            "citation_registry": citation_registry,
            "hallucinated_citations": hallucinated,
            "report_id": report_id,
            "validation": validation_result
        }

    except LLMTimeoutError as e:
        print(f"Judge Agent TIMEOUT: {e}")
        import traceback
        traceback.print_exc()

        return create_fallback_response(state, citation_registry, str(e))

    except Exception as e:
        print(f"Error in Judge Agent: {e}")
        import traceback
        traceback.print_exc()

        if hasattr(e, 'errors'):
            print(f"Validation Errors: {e.errors()}")

        return create_fallback_response(state, citation_registry, str(e))


def create_fallback_response(
    state: AgentState,
    citation_registry: Dict[str, Any],
    error_message: str
) -> Dict[str, Any]:
    """Create a fallback response when the main LLM call fails."""
    persona = state.get('analysis_persona', 'INVESTOR')
    config = get_persona_config(persona)

    print("Using Fallback Judge Response")

    # Create minimal fallback output
    fallback_decision = JudgeDecisionOutput(
        decision=config['decision_options'][2] if len(config['decision_options']) > 2 else config['decision_options'][0],  # Usually HOLD/MONITOR
        confidence_score=25,
        confidence_reasoning=f"System error prevented full analysis: {error_message}",
        justification=f"Analysis could not be completed due to: {error_message}. Manual review recommended.",
        key_concerns=["System error - manual review required"],
        summary=f"**Fallback Report**: The Judge Agent encountered an error. The system fallback mechanism activated. Error: {error_message}",
        bull_case="Analysis pending - system fallback active.",
        bear_case="Analysis pending - system fallback active.",
        risk_factors="Unable to assess - technical issues encountered.",
        analysis_focus_area="System Fallback"
    )

    final_output = build_final_output(state, fallback_decision, citation_registry)

    # Save fallback report
    report_id = save_report_to_db(state, final_output, fallback_decision)

    return {
        "final_report": fallback_decision.summary,
        "final_output_json": final_output.model_dump(),
        "citation_registry": citation_registry,
        "hallucinated_citations": [],
        "report_id": report_id,
        "errors": [error_message]
    }
