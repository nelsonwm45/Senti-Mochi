
from typing import TypedDict, Annotated, List, Optional
from uuid import UUID
import operator

class AgentState(TypedDict):
    company_id: str  # UUID as string
    company_name: str
    job_id: Optional[str]  # Analysis job ID for status tracking
    analysis_persona: str  # INVESTOR, RELATIONSHIP_MANAGER, CREDIT_RISK, MARKET_ANALYST

    # Inputs/Data gathered
    news_data: Optional[str] # Raw or summarized news content
    financial_data: Optional[str] # Structured financial inputs
    claims_data: Optional[str] # RAG content from documents

    # Critique Outputs (Debate Phase)
    news_critique: Optional[str]
    financial_critique: Optional[str]
    claims_critique: Optional[str]

    # Agent Outputs (Narratives)
    news_analysis: Optional[str]
    financial_analysis: Optional[str]
    claims_analysis: Optional[str]

    # Final Output
    final_report: Optional[str]

    # Internal
    errors: List[str]
