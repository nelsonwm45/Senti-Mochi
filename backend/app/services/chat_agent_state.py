"""
Chat Agent State & Token Pruner for Agentic RAG.

Defines the shared state for the chat LangGraph workflow and
a token pruner utility to respect Groq's 6,000 token limit.
"""

from typing import TypedDict, List, Dict, Optional, Any


class ChatAgentState(TypedDict):
    """Shared state flowing through the chat agentic workflow."""

    # --- Input ---
    query: str
    user_id: str
    user_role: str  # e.g. "MARKET_ANALYST", "INVESTOR", etc.
    analysis_persona: str  # maps to AnalysisPersona
    company_ids: Optional[List[str]]  # detected company UUIDs
    document_ids: Optional[List[str]]  # user-selected document filter
    query_embedding: List[float]
    chat_history: List[Dict[str, str]]
    max_results: int

    # --- Router Decision ---
    routed_agents: List[str]  # e.g. ["financial_agent", "news_agent"]

    # --- Retrieved Docs (accumulated by agents) ---
    retrieved_docs: List[Dict[str, Any]]  # list of chunk dicts

    # --- Token Budget ---
    token_count: int  # estimated tokens of context so far

    # --- Messages for LLM ---
    messages: List[Dict[str, str]]

    # --- Final Output ---
    response: str
    citations: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Token Pruner – keeps context under Groq's 6,000 token hard limit
# ---------------------------------------------------------------------------

# Reserve tokens for: system prompt (~800), chat history (~400), query (~100),
# answer generation (max_tokens=1024). That leaves ~3,676 for context.
GROQ_TOTAL_LIMIT = 6000
RESERVED_TOKENS = 2324  # system + history + query + generation headroom
MAX_CONTEXT_TOKENS = GROQ_TOTAL_LIMIT - RESERVED_TOKENS  # ≈ 3676


def estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 word ≈ 1.3 tokens."""
    return int(len(text.split()) * 1.3)


def prune_context(chunks: List[Dict[str, Any]], max_tokens: int = MAX_CONTEXT_TOKENS) -> List[Dict[str, Any]]:
    """
    Prune retrieved chunks so total context fits within *max_tokens*.

    Chunks are assumed to be pre-sorted by relevance (highest first).
    The pruner greedily keeps chunks until the budget is exhausted,
    then drops the rest.

    Returns:
        A (potentially shorter) list of chunks that fits the budget.
    """
    kept: List[Dict[str, Any]] = []
    running = 0

    for chunk in chunks:
        content = chunk.get("content", "")
        chunk_tokens = estimate_tokens(content)
        if running + chunk_tokens > max_tokens:
            break
        kept.append(chunk)
        running += chunk_tokens

    return kept
