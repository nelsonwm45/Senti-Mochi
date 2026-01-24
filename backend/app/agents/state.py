
from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# ============================================================
# FEATURE 1: Universal Citation Tracking - Core Models
# ============================================================

class CitedFact(BaseModel):
    """A fact with full citation provenance - the 'Source of Truth'"""
    content: str = Field(description="The extracted fact or claim")
    source_url: Optional[str] = Field(default=None, description="URL of the source")
    source_title: Optional[str] = Field(default=None, description="Title of the source document/article")
    source_date: Optional[str] = Field(default=None, description="Publication date of the source")
    source_type: str = Field(default="unknown", description="Type: 'news', 'financial', 'document'")
    page_number: Optional[int] = Field(default=None, description="Page number for documents")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score 0-1")
    citation_id: Optional[str] = Field(default=None, description="Unique citation marker e.g. [N1], [F2], [D3]")


class SourceReference(BaseModel):
    """Reference to a source used in analysis"""
    id: str = Field(description="Unique ID for this source e.g. 'N1', 'F2', 'D3'")
    type: str = Field(description="'news', 'financial', 'document'")
    title: str
    url: Optional[str] = None
    date: Optional[str] = None
    page: Optional[int] = None


# ============================================================
# FEATURE 3: Structured Debate Output Models
# ============================================================

class DebateArgument(BaseModel):
    """Single argument in the debate"""
    claim: str = Field(description="The main claim/argument")
    supporting_facts: List[str] = Field(default=[], description="Citation IDs supporting this claim")
    strength: str = Field(default="moderate", description="'strong', 'moderate', 'weak'")


class StructuredDebateOutput(BaseModel):
    """Structured debate following Government vs Opposition format"""
    bull_argument: DebateArgument = Field(description="The 'Government'/Pro stance")
    bear_argument: DebateArgument = Field(description="The 'Opposition'/Con stance")
    evidence_clash: List[str] = Field(default=[], description="Where the data conflicts")
    winning_side: Optional[str] = Field(default=None, description="'bull', 'bear', or 'undecided'")
    reasoning: Optional[str] = Field(default=None, description="Why this side won")


# ============================================================
# FEATURE 5: User Persona / Role Definition
# ============================================================

class AnalysisPersona(str, Enum):
    """Polymorphic analysis personas"""
    INVESTOR = "investor"  # Focus on growth, stock price, market sentiment
    CREDIT_RISK = "credit_risk"  # Focus on debt ratios, cash flow, bankruptcy risk
    RELATIONSHIP_MANAGER = "relationship_manager"  # Focus on talking points, news, relationship opportunities
    MARKET_ANALYST = "market_analyst"  # Focus on peer comparison, macro, relative valuation


class RoleWeights(BaseModel):
    """Scoring weights based on user role"""
    growth: float = 0.25
    profitability: float = 0.25
    debt_health: float = 0.25
    esg: float = 0.15
    sentiment: float = 0.10


def get_role_weights(role: AnalysisPersona) -> RoleWeights:
    """Get scoring weights based on user role for polymorphic analysis"""
    if role == AnalysisPersona.INVESTOR:
        return RoleWeights(
            growth=0.30,
            profitability=0.25,
            debt_health=0.15,
            esg=0.15,
            sentiment=0.15
        )
    elif role == AnalysisPersona.CREDIT_RISK:
        return RoleWeights(
            growth=0.10,
            profitability=0.20,
            debt_health=0.40,  # Higher weight for debt/cash flow
            esg=0.15,
            sentiment=0.15
        )
    elif role == AnalysisPersona.RELATIONSHIP_MANAGER:
        return RoleWeights(
            growth=0.15,
            profitability=0.15,
            debt_health=0.15,
            esg=0.20,
            sentiment=0.35  # Higher weight for news/talking points
        )
    elif role == AnalysisPersona.MARKET_ANALYST:
        return RoleWeights(
            growth=0.20,
            profitability=0.20,
            debt_health=0.20,
            esg=0.20,
            sentiment=0.20   # Balanced view
        )
    return RoleWeights()


# ============================================================
# FEATURE 2: Judge-Loop State Tracking
# ============================================================

class LoopbackInstruction(BaseModel):
    """Instructions for research loopback when Judge needs more data"""
    target_agent: str = Field(description="'news', 'financial', or 'claims'")
    research_query: str = Field(description="Specific research question to answer")
    context: str = Field(default="", description="Context from the debate that triggered this")


# ============================================================
# Main Agent State (Enhanced)
# ============================================================

class AgentState(TypedDict):
    """Enhanced Agent State with citation tracking and cyclic loop support"""

    # Core identifiers
    company_id: str  # UUID as string
    company_name: str
    job_id: Optional[str]  # Analysis job ID for status tracking

    # FEATURE 5: User Role for polymorphic analysis
    user_role: Optional[str]  # 'investor', 'credit_risk', 'relationship_manager'

    # FEATURE 1: Cited Facts (Source of Truth)
    # Each agent now stores structured facts with citations
    news_facts: Optional[List[dict]]  # List of CitedFact dicts
    financial_facts: Optional[List[dict]]  # List of CitedFact dicts
    claims_facts: Optional[List[dict]]  # List of CitedFact dicts

    # Source registry for the entire analysis
    sources: Optional[List[dict]]  # List of SourceReference dicts

    # Legacy: Raw analysis strings (kept for backwards compatibility)
    news_data: Optional[str]
    financial_data: Optional[str]
    claims_data: Optional[str]

    # Agent Analysis Outputs (narratives with embedded citations)
    news_analysis: Optional[str]
    financial_analysis: Optional[str]
    claims_analysis: Optional[str]

    # FEATURE 3: Structured Debate Outputs
    news_debate: Optional[dict]  # StructuredDebateOutput dict
    financial_debate: Optional[dict]  # StructuredDebateOutput dict
    claims_debate: Optional[dict]  # StructuredDebateOutput dict

    # Legacy Critique Outputs (kept for backwards compatibility)
    news_critique: Optional[str]
    financial_critique: Optional[str]
    claims_critique: Optional[str]

    # FEATURE 2: Judge-Loop Control
    loop_count: Optional[int]  # Current iteration count
    max_loops: Optional[int]  # Maximum allowed loops (default 3)
    needs_loopback: Optional[bool]  # Flag for conditional edge
    loopback_instruction: Optional[dict]  # LoopbackInstruction dict
    judge_decision: Optional[str]  # 'sufficient', 'needs_news', 'needs_financial', 'needs_claims'

    # Final Output
    final_report: Optional[str]

    # FEATURE 4: Verdict for Flip Card UI
    verdict: Optional[dict]  # Verdict dict with action, headline, deep_dive

    # Internal
    errors: List[str]
