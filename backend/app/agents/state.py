"""
Agent State Module for the Citation-First Analysis Engine.

This module defines the shared state that flows through the LangGraph workflow.
The state includes a global citation_registry that accumulates source metadata
from all agents, enabling end-to-end citation tracking.
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from uuid import UUID
import operator
from .citation_models import EvidencePoint


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
    user_id: Optional[str]  # User ID for ownership tracking
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
    # PHASE 1: RAW EVIDENCE (Ground Truth for Judge)
    # ==========================================================================
    # Structured evidence points extracted by researchers
    raw_evidence: Dict[str, List['EvidencePoint']]  # keys: 'news', 'financial', 'claims'

    # ==========================================================================
    # AGENT OUTPUTS (Narratives with embedded citations)
    # ==========================================================================
    # Each analysis contains embedded [N#], [F#], [D#] citations
    news_analysis: Optional[str]
    financial_analysis: Optional[str]
    claims_analysis: Optional[str]

    # ==========================================================================
    # CRITIQUE OUTPUTS (Legacy - kept for backward compat if needed)
    # ==========================================================================
    news_critique: Optional[str]
    financial_critique: Optional[str]
    claims_critique: Optional[str]

    # ==========================================================================
    # PHASE 2: LEGAL BRIEFS (Consolidated Evidence)
    # ==========================================================================
    # Consolidated lists of PROs and CONs for the lawyers
    legal_briefs: Dict[str, List[str]]  # keys: 'government', 'opposition'

    # ==========================================================================
    # PHASE 3: DEBATE OUTPUTS (Structured debate content)
    # ==========================================================================
    government_arguments: Optional[List[str]]  # Pro/bullish arguments with citations
    opposition_arguments: Optional[List[str]]  # Skeptic/bearish arguments with citations
    debate_transcript: Optional[List[str]]  # Full transcript of the debate loop

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
