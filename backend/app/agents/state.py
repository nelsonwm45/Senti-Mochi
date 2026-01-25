"""
Agent State Module for the Citation-First Analysis Engine.

This module defines the shared state that flows through the LangGraph workflow.
The state includes a global citation_registry that accumulates source metadata
from all agents, enabling end-to-end citation tracking.
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from uuid import UUID
import operator


class AgentState(TypedDict):
    """
    Shared state for the multi-agent analysis workflow.

    The citation_registry is a global dictionary that accumulates source metadata
    from all agents. Each agent appends its sources with unique IDs:
    - News Agent: [N1], [N2], ... -> {url, title, date}
    - Financial Agent: [F1], [F2], ... -> {document_name, row_line}
    - Claims Agent: [D1], [D2], ... -> {file_name, page_number, file_link}
    """
    company_id: str  # UUID as string
    company_name: str
    job_id: Optional[str]  # Analysis job ID for status tracking
    analysis_persona: str  # INVESTOR, RELATIONSHIP_MANAGER, CREDIT_RISK, MARKET_ANALYST

    # ==========================================================================
    # CITATION REGISTRY - Global source tracking
    # ==========================================================================
    # Maps citation IDs to SourceMetadata dicts
    # Example: {"N1": {"id": "N1", "title": "Bloomberg Article", "url_or_path": "https://...", "type": "News"}}
    citation_registry: Dict[str, Dict[str, Any]]

    # ==========================================================================
    # INPUTS/DATA GATHERED (Raw data for agents)
    # ==========================================================================
    news_data: Optional[str]  # Raw or summarized news content
    financial_data: Optional[str]  # Structured financial inputs
    claims_data: Optional[str]  # RAG content from documents

    # ==========================================================================
    # AGENT OUTPUTS (Narratives with embedded citations)
    # ==========================================================================
    # Each analysis contains embedded [N#], [F#], [D#] citations
    news_analysis: Optional[str]
    financial_analysis: Optional[str]
    claims_analysis: Optional[str]

    # ==========================================================================
    # CRITIQUE OUTPUTS (Debate Phase)
    # ==========================================================================
    news_critique: Optional[str]
    financial_critique: Optional[str]
    claims_critique: Optional[str]

    # ==========================================================================
    # DEBATE OUTPUTS (Structured debate content)
    # ==========================================================================
    government_arguments: Optional[List[str]]  # Pro/bullish arguments with citations
    opposition_arguments: Optional[List[str]]  # Skeptic/bearish arguments with citations

    # ==========================================================================
    # FINAL OUTPUT
    # ==========================================================================
    final_report: Optional[str]
    final_output_json: Optional[Dict[str, Any]]  # FinalAnalysisOutput as dict

    # ==========================================================================
    # INTERNAL/ERRORS
    # ==========================================================================
    errors: List[str]
    hallucinated_citations: List[str]  # Citations found in text but not in registry
