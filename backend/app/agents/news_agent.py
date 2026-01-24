
from typing import Dict, Any, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import NewsArticle, NewsChunk, Company
from app.agents.base import get_llm
from app.agents.state import AgentState, CitedFact, SourceReference, StructuredDebateOutput, DebateArgument
from app.agents.cache import generate_cache_key, hash_content, get_cached_result, set_cached_result
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
import json


class NewsExtraction(BaseModel):
    """Structured output for news analysis with citations"""
    key_events: List[str] = Field(default=[], description="Key events with citation markers")
    market_sentiment: str = Field(default="neutral", description="Overall sentiment: positive, negative, neutral")
    risks: List[str] = Field(default=[], description="Identified risks with citation markers")
    opportunities: List[str] = Field(default=[], description="Identified opportunities with citation markers")
    summary: str = Field(description="Executive summary with embedded citations")


def news_agent(state: AgentState) -> Dict[str, Any]:
    """
    Fetches recent news and generates an analysis with full citation tracking.
    FEATURE 1: Every fact now carries source URL, title, and date.
    """
    print(f"News Agent: Analyzing for company {state['company_name']} ({state['company_id']})")

    # FEATURE 5: Polymorphic Analysis Search Focus
    user_role = state.get("user_role", "investor")
    
    role_search_map = {
        "investor": ["M&A Rumors", "Product Launches", "Market Sentiment", "Analyst Upgrades", "Earnings Surprise"],
        "relationship_manager": ["New CEO", "Management Changes", "Office Expansion", "Awards", "Crisis Management", "CSR Initiatives"],
        "credit_risk": ["Litigation", "Fines", "Regulatory Bans", "Tariffs", "Fraud Allegations", "Credit Rating Downgrade"],
        "market_analyst": ["Macroeconomic Factors", "Foreign Exchange Exposure", "Supply Chain Disruptions", "Competitor Market Share"]
    }
    
    # Base queries + Role specific queries
    search_queries = [
        f"{state['company_name']} financial news",
        f"{state['company_name']} market sentiment",
    ]
    
    role_topics = role_search_map.get(user_role, role_search_map["investor"])
    for topic in role_topics:
        search_queries.append(f"{state['company_name']} {topic}")
        
    print(f"News Focus ({user_role}): Targeting {role_topics}")

    sources: List[dict] = state.get('sources', []) or []
    news_facts: List[dict] = []

    with Session(engine) as session:
        # Fetch recent 5 articles
        statement = (
            select(NewsArticle)
            .where(NewsArticle.company_id == state["company_id"])
            .order_by(col(NewsArticle.published_at).desc())
            .limit(5)
        )
        articles = session.exec(statement).all()

        if not articles:
            return {
                "news_analysis": "No recent news found for this company.",
                "news_facts": [],
                "sources": sources
            }

        # Build citation-aware context
        news_content = []
        for idx, article in enumerate(articles):
            citation_id = f"N{idx + 1}"

            # Register this source
            source_ref = SourceReference(
                id=citation_id,
                type="news",
                title=article.title,
                url=article.url,
                date=str(article.published_at.date()) if article.published_at else None
            )
            sources.append(source_ref.model_dump())

            # Collect chunks
            chunk_stmt = (
                select(NewsChunk)
                .where(NewsChunk.news_id == article.id)
                .order_by(NewsChunk.chunk_index)
            )
            chunks = session.exec(chunk_stmt).all()

            if chunks:
                article_text = "\n".join([c.content for c in chunks])
            else:
                article_text = article.content or ""

            # Truncate per-article to manage token limits
            if len(article_text) > 2000:
                article_text = article_text[:2000] + "..."

            # Format with citation ID for LLM context
            news_content.append(
                f"[{citation_id}] Date: {article.published_at.date() if article.published_at else 'Unknown'}\n"
                f"Title: {article.title}\n"
                f"URL: {article.url}\n"
                f"Content:\n{article_text}\n---"
            )

            # Create a base cited fact for this article
            fact = CitedFact(
                content=f"Article: {article.title}",
                source_url=article.url,
                source_title=article.title,
                source_date=str(article.published_at.date()) if article.published_at else None,
                source_type="news",
                confidence=0.9,
                citation_id=citation_id
            )
            news_facts.append(fact.model_dump())

        # Semantic Search for extra context (with citations)
        try:
            from app.services.embedding_service import embedding_service

            query = f"Key risks, financial performance, major events, ESG controversies for {state['company_name']}"
            query_vec = embedding_service.generate_embeddings([query])[0]

            vector_stmt = (
                select(NewsChunk)
                .join(NewsArticle)
                .where(NewsArticle.company_id == state["company_id"])
                .order_by(NewsChunk.embedding.l2_distance(query_vec))
                .limit(5)
            )

            relevant_chunks = session.exec(vector_stmt).all()

            if relevant_chunks:
                news_content.append("\n### Relevant Excerpts (Semantic Search):")
                for rc in relevant_chunks:
                    # Try to find parent article for citation
                    parent = session.get(NewsArticle, rc.news_id)
                    if parent:
                        # Find existing citation or create new
                        existing = next((s for s in sources if s.get('url') == parent.url), None)
                        if existing:
                            cid = existing['id']
                        else:
                            cid = f"N{len([s for s in sources if s['type'] == 'news']) + 1}"
                            sources.append(SourceReference(
                                id=cid, type="news", title=parent.title,
                                url=parent.url, date=str(parent.published_at.date()) if parent.published_at else None
                            ).model_dump())
                        news_content.append(f"- [{cid}] ...{rc.content[:500]}...")

        except Exception as e:
            print(f"Vector search failed (ignoring): {e}")

    context = "\n".join(news_content)

    # Generate cache key based on content hash
    content_hash = hash_content(context)
    cache_key = generate_cache_key("news_v2", state["company_id"], content_hash)

    # Check cache first
    cached_result = get_cached_result(cache_key)
    if cached_result:
        try:
            cached_data = json.loads(cached_result)
            return {
                "news_analysis": cached_data.get("analysis", cached_result),
                "news_facts": cached_data.get("facts", news_facts),
                "sources": cached_data.get("sources", sources)
            }
        except:
            return {"news_analysis": cached_result, "news_facts": news_facts, "sources": sources}

    # Token limit: ~3750 tokens = 15000 chars for Groq 6000 TPM
    if len(context) > 12000:
        context = context[:12000] + "..."

    prompt = f"""You are a News Analyst. 
    ROLE FOCUS: The user is a {user_role}. Prioritize news related to: {', '.join(role_topics)}.

    Analyze the following recent news articles for {state['company_name']}.

CRITICAL INSTRUCTION - CITATION RULES:
- Each article has a citation ID like [N1], [N2], etc.
- You MUST cite sources when making claims using these IDs.
- Example: "The company announced layoffs [N1]" or "Revenue grew 15% [N2]"

News Context:
{context}

Provide a concise analysis in Markdown that:
1. Identifies KEY EVENTS (with citations)
2. Assesses MARKET SENTIMENT (positive/negative/neutral)
3. Lists POTENTIAL RISKS (with citations)
4. Lists OPPORTUNITIES (with citations)
5. Executive SUMMARY (2-3 sentences with key citations)

IMPORTANT: Every claim must have at least one citation marker like [N1], [N2], etc."""

    llm = get_llm("llama-3.1-8b-instant")
    response = llm.invoke([
        SystemMessage(content="You are a financial news analyst. Always cite sources using [N1], [N2] format."),
        HumanMessage(content=prompt)
    ])

    analysis = response.content

    # Cache the result with metadata
    cache_data = json.dumps({
        "analysis": analysis,
        "facts": news_facts,
        "sources": sources
    })
    set_cached_result(cache_key, cache_data)

    return {
        "news_analysis": analysis,
        "news_facts": news_facts,
        "sources": sources
    }


def news_debate(state: AgentState) -> Dict[str, Any]:
    """
    FEATURE 3: Structured Debate - News Agent provides Bull/Bear arguments.
    Critiques other agents' findings and outputs structured debate format.
    """
    print(f"News Agent: Structured debate for {state['company_name']}")

    financial_analysis = state.get("financial_analysis", "No financial analysis provided.")
    claims_analysis = state.get("claims_analysis", "No claims analysis provided.")
    my_analysis = state.get("news_analysis", "No news analysis provided.")

    # Truncate inputs to stay within token limits
    if len(financial_analysis) > 3000:
        financial_analysis = financial_analysis[:3000] + "..."
    if len(claims_analysis) > 3000:
        claims_analysis = claims_analysis[:3000] + "..."
    if len(my_analysis) > 3000:
        my_analysis = my_analysis[:3000] + "..."

    prompt = f"""You are a News Analyst participating in an investment debate.
    ROLE FOCUS: You are arguing from the perspective of a {state.get('user_role', 'investor')}.

    Based on the analyses provided, construct a STRUCTURED DEBATE output.

1. NEWS ANALYSIS (Your Context):
{my_analysis}

2. FINANCIAL ANALYSIS:
{financial_analysis}

3. CLAIMS/DOCUMENTS ANALYSIS:
{claims_analysis}

OUTPUT FORMAT (JSON):
{{
    "bull_argument": {{
        "claim": "Main bullish thesis from news perspective",
        "supporting_facts": ["[N1]", "[N2]"],
        "strength": "strong|moderate|weak"
    }},
    "bear_argument": {{
        "claim": "Main bearish thesis from news perspective",
        "supporting_facts": ["[N1]"],
        "strength": "strong|moderate|weak"
    }},
    "evidence_clash": ["List conflicts between news and other analyses"],
    "winning_side": "bull|bear|undecided",
    "reasoning": "Why this side is stronger based on news signals"
}}

Respond ONLY with valid JSON."""

    llm = get_llm("llama-3.1-8b-instant")
    response = llm.invoke([
        SystemMessage(content="You output structured JSON for investment debates."),
        HumanMessage(content=prompt)
    ])

    # Parse response
    try:
        debate_output = json.loads(response.content)
    except:
        # Fallback structure
        debate_output = {
            "bull_argument": {"claim": "Positive news sentiment", "supporting_facts": [], "strength": "moderate"},
            "bear_argument": {"claim": "Market uncertainty", "supporting_facts": [], "strength": "moderate"},
            "evidence_clash": [],
            "winning_side": "undecided",
            "reasoning": response.content[:500]
        }

    return {"news_debate": debate_output, "news_critique": response.content}


def news_critique(state: AgentState) -> Dict[str, Any]:
    """
    Legacy critique function - now calls news_debate for structured output.
    Kept for backwards compatibility.
    """
    return news_debate(state)
