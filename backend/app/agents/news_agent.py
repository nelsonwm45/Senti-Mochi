"""
News Agent - The Scout

Fetches and analyzes recent news articles with citation tracking.
Generates [N1], [N2], ... citations mapping to {url, title, date}.
Focus: Market Sentiment and Recent Scandals.
"""

from typing import Dict, Any, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import NewsArticle, NewsChunk, Company
from app.agents.base import get_llm
from app.agents.state import AgentState
from app.agents.cache import generate_cache_key, hash_content, get_cached_result, set_cached_result
from app.agents.persona_config import get_persona_config
from app.agents.prompts import NEWS_AGENT_SYSTEM, get_news_agent_prompt, get_critique_prompt
from app.agents.citation_models import SourceMetadata
from app.services.news_relevance import news_relevance_filter
from app.services.content_optimizer import content_optimizer
from langchain_core.messages import SystemMessage, HumanMessage


def news_agent(state: AgentState) -> Dict[str, Any]:
    """
    Fetches recent news and generates an analysis with citation tracking.

    Citation Protocol:
    - Each article gets an ID: [N1], [N2], [N3], etc.
    - Returns citation_registry updates with SourceMetadata

    Returns:
        Dict with news_analysis and citation_registry updates
    """
    persona = state.get('analysis_persona', 'INVESTOR')
    config = get_persona_config(persona)
    company_id = state["company_id"]
    company_name = state["company_name"]

    print(f"News Agent: Analyzing for {company_name} ({company_id}) [Persona: {persona}]")

    # Initialize citation registry if not present
    citation_registry = dict(state.get('citation_registry', {}))

    with Session(engine) as session:
        # Fetch recent articles (fetch more to allow for filtering)
        statement = (
            select(NewsArticle)
            .where(NewsArticle.company_id == company_id)
            .order_by(col(NewsArticle.published_at).desc())
            .limit(25)  # Fetch extra to account for filtering
        )
        articles = list(session.exec(statement).all())

        if not articles:
            return {
                "news_analysis": "No recent news found for this company.",
                "citation_registry": citation_registry
            }

        # Get company for relevance filtering
        company = session.get(Company, company_id)
        company_sector = company.sector if company else None

        # Filter for relevance (can be disabled for testing/debugging)
        # Only filter if we have many articles - let's be more lenient
        # Set DISABLE_NEWS_FILTER=true to skip filtering entirely
        import os
        disable_filter = os.getenv('DISABLE_NEWS_FILTER', 'false').lower() == 'true'
        
        if not disable_filter and company and len(articles) > 20:
            # Only filter if we have excess articles
            articles = news_relevance_filter.filter_news_articles_db(
                session, articles, company
            )
        elif disable_filter:
            print(f"[NEWS_AGENT] Relevance filtering DISABLED (DISABLE_NEWS_FILTER=true)")

        # Limit to top 15 most relevant/recent
        articles = articles[:15]

        if not articles:
            return {
                "news_analysis": "No relevant news found for this company after filtering.",
                "citation_registry": citation_registry
            }

        print(f"News Agent: Processing {len(articles)} relevant articles for {company_name}")

        # Build citation metadata and content
        news_content = []
        source_list_parts = []

        for idx, article in enumerate(articles, start=1):
            citation_id = f"N{idx}"

            # Create SourceMetadata for this article
            source_metadata = {
                "id": citation_id,
                "title": article.title,
                "url_or_path": article.url,
                "type": "News",
                "date": article.published_at.isoformat() if article.published_at else None
            }
            citation_registry[citation_id] = source_metadata

            # Add to source list for prompt
            source_list_parts.append(
                f"[{citation_id}] - \"{article.title}\" ({article.published_at.strftime('%Y-%m-%d') if article.published_at else 'Unknown date'})"
            )

            # Collect article content
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

            news_content.append(
                f"[{citation_id}] Date: {article.published_at}\n"
                f"Title: {article.title}\n"
                f"Content:\n{article_text}\n---"
            )

        # Semantic Search for extra context - PERSONA-AWARE
        try:
            from app.services.embedding_service import embedding_service

            query = f"{config['news_query']} for {company_name}"
            query_vec = embedding_service.generate_embeddings([query])[0]

            vector_stmt = (
                select(NewsChunk)
                .join(NewsArticle)
                .where(NewsArticle.company_id == company_id)
                .order_by(NewsChunk.embedding.l2_distance(query_vec))
                .limit(8)
            )

            relevant_chunks = session.exec(vector_stmt).all()

            if relevant_chunks:
                news_content.append("\n### Relevant Excerpts (Semantic Search):")
                for rc in relevant_chunks:
                    news_content.append(f"- ...{rc.content}...")

        except Exception as e:
            print(f"Vector search failed (ignoring): {e}")

    context = "\n".join(news_content)
    source_list = "\n".join(source_list_parts)

    # Generate cache key based on content hash
    content_hash = hash_content(context)
    cache_key = generate_cache_key("news_v3", company_id, content_hash)

    # Check cache first
    cached_result = get_cached_result(cache_key)
    if cached_result:
        return {
            "news_analysis": cached_result,
            "citation_registry": citation_registry
        }

    # Truncation Logic with Fallback Strategy
    # Cerebras supports 60k+ context, so we try that first WITHOUT truncation.
    # If it fails, we fallback to Groq and apply the strict truncation (3500 chars).
    
    # context is the full context
    full_context = context
    
    # Attempt Primary: Cerebras (llama-3.3-70b)
    try:
        print(f"[News Agent] Attempting to use Cerebras (llama-3.3-70b)...")
        # Reuse full context
        prompt = get_news_agent_prompt(
            company_name=company_name,
            persona=persona,
            news_context=full_context,
            source_list=source_list
        )
        
        llm = get_llm("llama-3.3-70b")
        response = llm.invoke([
            SystemMessage(content=NEWS_AGENT_SYSTEM),
            HumanMessage(content=prompt)
        ])
        print(f"[News Agent] SUCCESS: Processed by Cerebras (llama-3.3-70b)")
        
        # Cache the result
        set_cached_result(cache_key, response.content)

        return {
            "news_analysis": response.content,
            "citation_registry": citation_registry
        }

    except Exception as e:
        print(f"[News Agent] Cerebras failed: {e}. Fallback to Groq (llama-3.1-8b-instant)...")
        
        # Apply truncation for Groq
        truncated_context = content_optimizer._smart_truncate(full_context, 3500)
        
        prompt = get_news_agent_prompt(
            company_name=company_name,
            persona=persona,
            news_context=truncated_context,
            source_list=source_list
        )
        
        llm = get_llm("llama-3.1-8b-instant")
        response = llm.invoke([
            SystemMessage(content=NEWS_AGENT_SYSTEM),
            HumanMessage(content=prompt)
        ])
        print(f"[News Agent] SUCCESS: Processed by Groq (llama-3.1-8b-instant)")
        
        # Cache the result
        set_cached_result(cache_key, response.content)

        return {
            "news_analysis": response.content,
            "citation_registry": citation_registry
        }


def news_critique(state: AgentState) -> Dict[str, Any]:
    """
    Critiques other agents' findings based on News data.
    Preserves and references all citation IDs.
    """
    persona = state.get('analysis_persona', 'INVESTOR')
    persona_label = persona.replace('_', ' ').title()
    print(f"News Agent: Critiquing findings for {state['company_name']} [Persona: {persona}]")

    financial_analysis = state.get("financial_analysis", "No financial analysis provided.")
    claims_analysis = state.get("claims_analysis", "No claims analysis provided.")
    my_analysis = state.get("news_analysis", "No news analysis provided.")

    prompt = get_critique_prompt(
        agent_type="news",
        persona=persona,
        my_analysis=my_analysis,
        other_analysis_1=financial_analysis,
        other_analysis_2=claims_analysis,
        analysis_1_name="Financial Analysis",
        analysis_2_name="Claims Analysis"
    )

    llm = get_llm("llama-3.1-8b-instant")
    response = llm.invoke([
        SystemMessage(content=f"You are a critical news analyst serving a {persona_label}. PRESERVE all citation IDs."),
        HumanMessage(content=prompt)
    ])

    return {"news_critique": response.content}
