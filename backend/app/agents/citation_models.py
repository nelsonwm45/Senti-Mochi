"""
Citation-First Analysis Engine - Pydantic Data Models

This module defines the structured output schema for the Citation-First Analysis Engine.
Every claim must have a clickable citation. The output is structured for the Frontend UI
layout involving Role-Based insights, ESG deep dives, Financial health, and Debate transcript.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any


# =============================================================================
# CORE CITATION PRIMITIVES
# =============================================================================

class SourceMetadata(BaseModel):
    """
    Metadata for a single source citation.
    Maps citation IDs like [N1], [F1], [D1] to their source details.
    """
    id: str = Field(..., description="Citation ID e.g., 'N1', 'F1', 'D1'")
    title: str = Field(..., description="Title of the source (article title, document name, statement type)")
    url_or_path: str = Field(..., description="URL for news, file path for documents, or statement identifier for financials")
    type: Literal["News", "Financial", "Document"] = Field(..., description="Source type")
    # Extended metadata
    date: Optional[str] = Field(None, description="Publication date or period")
    page_number: Optional[int] = Field(None, description="Page number for document sources")
    row_line: Optional[str] = Field(None, description="Specific row/line reference for financial data")


class SectionContent(BaseModel):
    """
    Standard content structure for each analysis section.
    Used by ESG and Financial reports for consistent UI rendering.
    """
    preview_summary: str = Field(
        ...,
        description="1-2 sentence high-level summary for collapsed view"
    )
    detailed_findings: List[str] = Field(
        default_factory=list,
        description="Bullet points with embedded citation IDs like [N1], [F2], [D3]"
    )
    confidence_score: int = Field(
        default=50,
        ge=0,
        le=100,
        description="0-100 score on data availability/reliability"
    )
    highlights: List[str] = Field(
        default_factory=list,
        description="3-5 key metrics or data points (plain text, no markdown)"
    )


# =============================================================================
# UI SECTION 1: ROLE-BASED REPORT
# =============================================================================

class RoleBasedInsight(BaseModel):
    """
    Top-level insight card based on user's role/persona.
    This is the primary decision output shown at the top of the dashboard.
    """
    user_role: str = Field(
        ...,
        description="The persona used: INVESTOR, RELATIONSHIP_MANAGER, CREDIT_RISK, MARKET_ANALYST"
    )
    decision: str = Field(
        ...,
        description="Role-specific decision: BUY/SELL/HOLD, ENGAGE/MONITOR/AVOID, APPROVE/REJECT/COLLATERALIZE, OVERWEIGHT/UNDERWEIGHT"
    )
    justification: str = Field(
        ...,
        description="The 'Why' behind the decision with embedded citations like [N1], [F2]"
    )
    key_concerns: List[str] = Field(
        default_factory=list,
        description="Top 3-5 role-specific risks with citations e.g., 'Margin Compression [F1]', 'Regulatory fines [N2]'"
    )
    confidence_score: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Overall confidence in the decision"
    )


# =============================================================================
# UI SECTION 2: ESG REPORT
# =============================================================================

class ESGReport(BaseModel):
    """
    Comprehensive ESG analysis with citation-backed findings.
    Each section follows the SectionContent structure for consistent UI.
    """
    overview: SectionContent = Field(
        default_factory=lambda: SectionContent(
            preview_summary="ESG data analysis pending.",
            detailed_findings=[],
            confidence_score=0
        ),
        description="Overall ESG posture summary"
    )
    governance_integration: SectionContent = Field(
        default_factory=lambda: SectionContent(
            preview_summary="Governance analysis pending.",
            detailed_findings=[],
            confidence_score=0
        ),
        description="Board structure, executive pay, internal controls"
    )
    environmental: SectionContent = Field(
        default_factory=lambda: SectionContent(
            preview_summary="Environmental analysis pending.",
            detailed_findings=[],
            confidence_score=0
        ),
        description="Net Zero claims, carbon footprint, climate risks"
    )
    social: SectionContent = Field(
        default_factory=lambda: SectionContent(
            preview_summary="Social analysis pending.",
            detailed_findings=[],
            confidence_score=0
        ),
        description="Labor practices, community impact, DEI"
    )
    disclosure_quality: SectionContent = Field(
        default_factory=lambda: SectionContent(
            preview_summary="Disclosure quality pending.",
            detailed_findings=[],
            confidence_score=0
        ),
        description="Audit status, reporting transparency, data quality"
    )


# =============================================================================
# UI SECTION 3: FINANCIAL REPORT
# =============================================================================

class FinancialReport(BaseModel):
    """
    Comprehensive financial analysis with citation-backed findings.
    """
    valuation: SectionContent = Field(
        default_factory=lambda: SectionContent(
            preview_summary="Valuation analysis pending.",
            detailed_findings=[],
            confidence_score=0
        ),
        description="P/E, PEG, EV/EBITDA, DCF analysis"
    )
    profitability: SectionContent = Field(
        default_factory=lambda: SectionContent(
            preview_summary="Profitability analysis pending.",
            detailed_findings=[],
            confidence_score=0
        ),
        description="Net Margin, Gross Margin, ROE, ROIC"
    )
    growth: SectionContent = Field(
        default_factory=lambda: SectionContent(
            preview_summary="Growth analysis pending.",
            detailed_findings=[],
            confidence_score=0
        ),
        description="Revenue YoY, EPS YoY, market expansion"
    )
    financial_health: SectionContent = Field(
        default_factory=lambda: SectionContent(
            preview_summary="Financial health pending.",
            detailed_findings=[],
            confidence_score=0
        ),
        description="Debt-to-Equity, Quick Ratio, Interest Coverage, Altman Z-Score"
    )


# =============================================================================
# UI SECTION 4: MARKET SENTIMENT (from News)
# =============================================================================

class MarketSentiment(BaseModel):
    """
    Market sentiment derived from news analysis.
    Uses [N#] citations from news sources.
    """
    sentiment: str = Field(
        default="NEUTRAL",
        description="POSITIVE | NEUTRAL | NEGATIVE"
    )
    summary: str = Field(
        default="No recent news available.",
        description="2-3 sentences on market perception with [N#] citations"
    )
    key_events: List[str] = Field(
        default_factory=list,
        description="3-5 recent events affecting the company with [N#] citations"
    )
    risks_from_news: List[str] = Field(
        default_factory=list,
        description="2-3 news-based risks or concerns with [N#] citations"
    )



class EvidencePoint(BaseModel):
    """
    A single point of evidence extracted by Researcher Agents.
    Used to build the Ground Truth and Legal Briefs.
    """
    content: str = Field(..., description="The evidence claim/fact")
    citation: str = Field(..., description="Citation ID e.g., '[N1]'")
    sentiment: Literal["PRO", "CON"] = Field(..., description="Supports (PRO) or opposes (CON) the user's goal")
    confidence: int = Field(default=50, description="Confidence in this extraction (0-100)")


# =============================================================================
# UI SECTION 5: DEBATE REPORT
# =============================================================================

class DebateStance(BaseModel):
    """
    Represents one side of the debate (Government/Pro or Opposition/Skeptic).
    """
    stance_summary: str = Field(
        ...,
        description="1-2 sentence summary of the stance"
    )
    arguments: List[str] = Field(
        default_factory=list,
        description="List of arguments, each MUST contain [SourceID] citations"
    )


class DebateReport(BaseModel):
    """
    Structured debate transcript between Government (bullish) and Opposition (bearish).
    """
    government_stand: DebateStance = Field(
        default_factory=lambda: DebateStance(
            stance_summary="Pro-investment stance pending.",
            arguments=[]
        ),
        description="Bullish/Pro arguments from Financial Agent perspective"
    )
    opposition_stand: DebateStance = Field(
        default_factory=lambda: DebateStance(
            stance_summary="Skeptic stance pending.",
            arguments=[]
        ),
        description="Bearish/Skeptic arguments from News Agent perspective"
    )
    judge_verdict: str = Field(
        default="Verdict pending.",
        description="Final judge synthesis resolving the debate"
    )
    # Optional enhanced verdict fields
    verdict_reasoning: str = Field(
        default="",
        description="2-3 sentence explanation of why this verdict was reached"
    )
    verdict_key_factors: List[str] = Field(
        default_factory=list,
        description="3-5 key factors with citations [N#], [F#], [D#] that influenced the verdict"
    )
    transcript: Optional[str] = Field(
        None,
        description="Full markdown transcript of the debate (Government vs Opposition)"
    )


# =============================================================================
# MASTER OUTPUT - FINAL ANALYSIS OUTPUT
# =============================================================================

class FinalAnalysisOutput(BaseModel):
    """
    Master output schema for the Citation-First Analysis Engine.
    This is the complete JSON contract that powers the Frontend UI.
    """
    company_name: str = Field(..., description="Name of the analyzed company")
    company_id: str = Field(..., description="UUID of the company")
    analysis_timestamp: str = Field(..., description="ISO timestamp of when analysis was generated")

    # Core Reports
    role_report: RoleBasedInsight = Field(
        ...,
        description="Role-specific decision card (top of dashboard)"
    )
    esg_report: ESGReport = Field(
        default_factory=ESGReport,
        description="ESG analysis accordion section"
    )
    financial_report: FinancialReport = Field(
        default_factory=FinancialReport,
        description="Financial analysis accordion section"
    )
    market_sentiment: MarketSentiment = Field(
        default_factory=MarketSentiment,
        description="Market sentiment from news analysis with [N#] citations"
    )
    debate_report: DebateReport = Field(
        default_factory=DebateReport,
        description="Debate transcript section"
    )

    # Citation Registry - The lookup table for the frontend
    citation_registry: Dict[str, SourceMetadata] = Field(
        default_factory=dict,
        description="Global registry mapping citation IDs to source metadata. Frontend uses this to render clickable citations."
    )

    # Legacy compatibility fields (for existing frontend)
    rating: Optional[str] = Field(None, description="Legacy: Same as role_report.decision")
    confidence_score: Optional[int] = Field(None, description="Legacy: Same as role_report.confidence_score")
    summary: Optional[str] = Field(None, description="Legacy: Executive summary")
    bull_case: Optional[str] = Field(None, description="Legacy: Bull case narrative")
    bear_case: Optional[str] = Field(None, description="Legacy: Bear case narrative")
    risk_factors: Optional[str] = Field(None, description="Legacy: Risk factors")


# =============================================================================
# AGENT OUTPUT MODELS (Intermediate)
# =============================================================================

class NewsAgentOutput(BaseModel):
    """Output from the News Agent with citation metadata."""
    analysis: str = Field(..., description="News analysis with embedded [N#] citations")
    sources: List[SourceMetadata] = Field(
        default_factory=list,
        description="List of news source metadata for the citation registry"
    )
    market_sentiment: Optional[str] = Field(None, description="Overall market sentiment: POSITIVE, NEGATIVE, NEUTRAL")
    recent_scandals: List[str] = Field(default_factory=list, description="List of recent scandals/issues found")


class FinancialAgentOutput(BaseModel):
    """Output from the Financial Agent with citation metadata."""
    analysis: str = Field(..., description="Financial analysis with embedded [F#] citations")
    sources: List[SourceMetadata] = Field(
        default_factory=list,
        description="List of financial document metadata for the citation registry"
    )
    key_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted key financial metrics"
    )


class ClaimsAgentOutput(BaseModel):
    """Output from the Claims/RAG Agent with citation metadata."""
    analysis: str = Field(..., description="Claims analysis with embedded [D#] citations")
    sources: List[SourceMetadata] = Field(
        default_factory=list,
        description="List of document chunk metadata for the citation registry"
    )
    governance_findings: List[str] = Field(default_factory=list)
    environmental_findings: List[str] = Field(default_factory=list)
    social_findings: List[str] = Field(default_factory=list)
    disclosure_quality: Optional[str] = Field(None, description="HIGH, MEDIUM, LOW")


# =============================================================================
# CITATION UTILITIES
# =============================================================================

def validate_citations(text: str, registry: Dict[str, SourceMetadata]) -> List[str]:
    """
    Validate that all citation IDs in text exist in the registry.
    Returns list of invalid citation IDs (hallucinations).

    Args:
        text: Text containing citation IDs like [N1], [F2], [D3]
        registry: The citation registry to validate against

    Returns:
        List of citation IDs found in text but missing from registry
    """
    import re
    # Match patterns like [N1], [F2], [D3], [N10], etc.
    citation_pattern = r'\[([NFD]\d+)\]'
    found_citations = set(re.findall(citation_pattern, text))

    invalid_citations = []
    for citation_id in found_citations:
        if citation_id not in registry:
            invalid_citations.append(citation_id)

    return invalid_citations


def merge_citation_registries(*registries: Dict[str, SourceMetadata]) -> Dict[str, SourceMetadata]:
    """
    Merge multiple citation registries into one.
    Later registries override earlier ones on key conflicts.
    """
    merged = {}
    for registry in registries:
        merged.update(registry)
    return merged


def extract_citations_from_text(text: str) -> List[str]:
    """
    Extract all citation IDs from a text string.

    Args:
        text: Text containing citation IDs like [N1], [F2], [D3]

    Returns:
        List of unique citation IDs found
    """
    import re
    citation_pattern = r'\[([NFD]\d+)\]'
    return list(set(re.findall(citation_pattern, text)))


# =============================================================================
# LEGAL TEAM ARCHITECTURE
# =============================================================================

class LegalBrief(BaseModel):
    """
    Consolidated brief for one side (Government or Opposition).
    Derived from raw evidence using the Briefing Node.
    """
    role: Literal["Government", "Opposition"]
    points: List[str] = Field(..., description="List of synthesized points/claims with preserved citations")
