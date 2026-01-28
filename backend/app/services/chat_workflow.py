"""
Agentic RAG Chat Workflow (LangGraph)

Flow:
  Start -> Router (Gemini Flash) -> [Agent1, Agent2, ...] -> Pruner -> Generation (Groq) -> End

The Router analyzes the user query + role and decides which domain agents to invoke.
Each agent appends chunks to state["retrieved_docs"].
The Pruner trims context to fit Groq's 6,000-token limit.
The Generator produces the final cited answer using Groq (Llama-3).
"""

import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List

from langgraph.graph import END, StateGraph

from app.services.chat_agent_state import (
    ChatAgentState,
    MAX_CONTEXT_TOKENS,
    estimate_tokens,
    prune_context,
)
from app.services.chat_agents import (
    claims_chat_agent,
    financial_chat_agent,
    news_chat_agent,
    report_chat_agent,
    sentiment_chat_agent,
)

# ---------------------------------------------------------------------------
# 1. Router Node – Gemini Flash (15 RPM on Free Tier)
# ---------------------------------------------------------------------------

ROUTER_SYSTEM = """You are a query router for a financial RAG chatbot. Analyze the user's query and role, then decide which specialist agents should handle it.

Available agents:
- financial_agent: For questions about financial statements, P/E ratios, revenue, earnings, balance sheets, cash flows, valuations.
- news_agent: For questions about recent news, events, headlines, announcements.
- claims_agent: For questions requiring search over the user's uploaded documents (PDFs, annual reports, internal docs).
- report_agent: For questions about past analysis reports, recommendations, bull/bear cases.
- sentiment_agent: For questions about market sentiment, mood, investor confidence, sentiment scores.

Rules:
- You may select 1-3 agents. Pick only what's relevant.
- If the query is general financial chat with no specific domain, select ["claims_agent", "financial_agent"].
- If the query mentions "sentiment", "mood", "confidence", always include sentiment_agent.
- If the query mentions "report", "analysis", "recommendation", always include report_agent.
- If the query mentions "news", "latest", "headline", "announcement", always include news_agent.

Respond ONLY with a JSON object: {"agents": ["agent_name1", "agent_name2"]}
No other text."""


def _call_gemini_with_retry(prompt: str, max_retries: int = 3) -> str:
    """Call Gemini Flash with exponential backoff for 429 errors."""
    from app.agents.base import get_llm
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm("gemini-2.0-flash")

    for attempt in range(max_retries):
        try:
            response = llm.invoke([
                SystemMessage(content=ROUTER_SYSTEM),
                HumanMessage(content=prompt),
            ])
            return response.content
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Resource Exhausted" in error_str.lower() or "resource_exhausted" in error_str.lower():
                wait = 2 ** attempt  # 1s, 2s, 4s (reduced from 2s, 4s, 8s)
                print(f"[Router] Gemini 429 – retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
            else:
                raise
    # If all retries exhausted, fall back to default routing
    print("[Router] Gemini retries exhausted – falling back to default agents")
    return '{"agents": ["claims_agent", "financial_agent", "news_agent"]}'


def router_node(state: ChatAgentState) -> Dict[str, Any]:
    """
    Analyze the query + user_role and decide which agents to invoke.
    Uses Gemini Flash for fast, cheap classification.
    """
    query = state["query"]
    user_role = state.get("user_role", "USER")
    persona = state.get("analysis_persona", "INVESTOR")

    prompt = (
        f"User Role: {user_role}\n"
        f"Analysis Persona: {persona}\n"
        f"User Query: {query}\n\n"
        f"Which agents should handle this query?"
    )

    try:
        raw = _call_gemini_with_retry(prompt)
        # Parse JSON from response (handle markdown code blocks)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"```(?:json)?", "", raw).strip()
        parsed = json.loads(raw)
        agents = parsed.get("agents", [])
    except Exception as e:
        print(f"[Router] Parse error: {e} – using defaults")
        agents = ["claims_agent", "financial_agent"]

    valid = {"financial_agent", "news_agent", "claims_agent", "report_agent", "sentiment_agent"}
    agents = [a for a in agents if a in valid]
    if not agents:
        agents = ["claims_agent", "financial_agent"]

    print(f"[Router] Query: '{query[:60]}...' -> Agents: {agents}")
    return {"routed_agents": agents}


# ---------------------------------------------------------------------------
# 2. Agent Dispatcher – runs the selected agents sequentially
# ---------------------------------------------------------------------------

AGENT_MAP = {
    "financial_agent": financial_chat_agent,
    "news_agent": news_chat_agent,
    "claims_agent": claims_chat_agent,
    "report_agent": report_chat_agent,
    "sentiment_agent": sentiment_chat_agent,
}


def agent_dispatcher(state: ChatAgentState) -> Dict[str, Any]:
    """Run each routed agent in sequence, accumulating retrieved_docs."""
    routed = state.get("routed_agents", [])
    # Start with empty docs for this dispatch
    current_state = dict(state)
    current_state["retrieved_docs"] = list(state.get("retrieved_docs", []))

    for agent_name in routed:
        fn = AGENT_MAP.get(agent_name)
        if fn:
            try:
                result = fn(current_state)
                current_state["retrieved_docs"] = result.get("retrieved_docs", current_state["retrieved_docs"])
            except Exception as e:
                print(f"[Dispatcher] Agent {agent_name} failed: {e}")

    return {"retrieved_docs": current_state["retrieved_docs"]}


# ---------------------------------------------------------------------------
# 3. Context Pruner Node – enforces Groq token budget
# ---------------------------------------------------------------------------

def pruner_node(state: ChatAgentState) -> Dict[str, Any]:
    """Prune retrieved docs to fit Groq's 6,000 token limit."""
    docs = state.get("retrieved_docs", [])

    # Sort by similarity descending so most relevant survive
    docs_sorted = sorted(docs, key=lambda d: d.get("similarity", 0), reverse=True)
    pruned = prune_context(docs_sorted, MAX_CONTEXT_TOKENS)

    total_tokens = sum(estimate_tokens(d.get("content", "")) for d in pruned)
    print(f"[Pruner] {len(docs)} docs -> {len(pruned)} kept ({total_tokens} est. tokens)")

    return {"retrieved_docs": pruned, "token_count": total_tokens}


# ---------------------------------------------------------------------------
# 4. Generation Node – Groq (Llama-3)
# ---------------------------------------------------------------------------

def generation_node(state: ChatAgentState) -> Dict[str, Any]:
    """Build the final response with Groq, preserving [Source N] citations."""
    import openai

    client = openai.OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )

    docs = state.get("retrieved_docs", [])
    query = state["query"]
    chat_history = state.get("chat_history", [])

    # Build context string with [Source N] labels
    context_parts = []
    for i, chunk in enumerate(docs):
        context_parts.append(
            f"[Source {i + 1}: {chunk.get('filename', 'Unknown')}, "
            f"Page {chunk.get('page_number', 'N/A')}]\n"
            f"{chunk['content']}\n"
        )
    context = "\n---\n".join(context_parts)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    prompt = f"""
Role: You are a Senior Market Intelligence Analyst. Your purpose is to provide end-to-end market analysis, helping banking teams transform unstructured market signals into defensible, consistent investment or strategic decisions.

Current Time: {current_time}

CRITICAL ADHERENCE RULES
1. Strict Domain Focus: You are prohibited from answering general knowledge questions (e.g., "What is the capital of France?" or "How do I bake a cake?").
2. Redirection Protocol: If a user asks a general or non-finance question, you must provide a polite, single-sentence acknowledgment of the query, followed immediately by a redirection to your core functions.
3. Standard Refusal: "I specialize in market intelligence and banking-grade financial analysis. Please provide a ticker, sector, or market signal for me to analyze."
4. Data-Driven Responses: Always prioritize provided context (documents, news, financials). If the data is present, answer with institutional-grade confidence.
5. No Hallucinations: If data is missing for a calculation or analysis, state "Data Not Available." Never guess.
6. PII Protection: Redact any sensitive information (e.g., account numbers) and warn the user immediately.

OUTPUT FORMATTING
1. Calculations: Must show the formula and step-by-step math.
2. Data Extraction: If the user requests data parsing, output strictly in JSON format with no conversational filler.
3. Tone: Maintain an institutional, objective tone. Use terms like "high volatility" or "strategic alignment" instead of "exciting" or "massive."

CITATION PROTOCOL
1. Only cite sources using the [Source N] format if the information is explicitly found in the provided context.
2. If no context is provided, answer using internal knowledge but do not use citations.

Context:
{context if context else "[No relevant documents found]"}

---

User Question: {query}

Answer (cite sources as [Source 1], [Source 2], etc.):"""

    messages = [{"role": "system", "content": "You are a helpful finance expert assistant."}]
    if chat_history:
        for msg in chat_history:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content
    tokens_used = response.usage.total_tokens if hasattr(response, "usage") and response.usage else None

    return {
        "response": answer,
        "token_count": tokens_used or state.get("token_count", 0),
    }


# ---------------------------------------------------------------------------
# 5. Build the LangGraph
# ---------------------------------------------------------------------------

def build_chat_graph():
    """
    Start -> Router -> Dispatcher -> Pruner -> Generation -> END
    """
    builder = StateGraph(ChatAgentState)

    builder.add_node("router", router_node)
    builder.add_node("dispatcher", agent_dispatcher)
    builder.add_node("pruner", pruner_node)
    builder.add_node("generation", generation_node)

    builder.set_entry_point("router")
    builder.add_edge("router", "dispatcher")
    builder.add_edge("dispatcher", "pruner")
    builder.add_edge("pruner", "generation")
    builder.add_edge("generation", END)

    return builder.compile()


# Singleton compiled graph
chat_graph = build_chat_graph()


def run_chat_agentic(
    query: str,
    user_id: str,
    user_role: str,
    analysis_persona: str,
    query_embedding: List[float],
    chat_history: List[Dict[str, str]],
    company_ids: List[str] | None = None,
    document_ids: List[str] | None = None,
    max_results: int = 5,
) -> Dict[str, Any]:
    """
    Public entry-point: run the agentic RAG pipeline and return the result.

    Returns dict with keys: response, retrieved_docs, token_count, routed_agents.
    """
    initial_state: ChatAgentState = {
        "query": query,
        "user_id": user_id,
        "user_role": user_role,
        "analysis_persona": analysis_persona,
        "company_ids": [str(c) for c in company_ids] if company_ids else [],
        "document_ids": [str(d) for d in document_ids] if document_ids else [],
        "query_embedding": query_embedding,
        "chat_history": chat_history,
        "max_results": max_results,
        "routed_agents": [],
        "retrieved_docs": [],
        "token_count": 0,
        "messages": [],
        "response": "",
        "citations": [],
    }

    result = chat_graph.invoke(initial_state)
    return result
