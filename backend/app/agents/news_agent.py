
from typing import Dict, Any
from sqlmodel import Session, select, col
from app.database import engine
from app.models import NewsArticle, NewsChunk, Company
from app.agents.base import get_llm
from app.agents.state import AgentState
from app.agents.cache import generate_cache_key, hash_content, get_cached_result, set_cached_result
from langchain_core.messages import SystemMessage, HumanMessage

def news_agent(state: AgentState) -> Dict[str, Any]:
    """
    Fetches recent news and generates an analysis.
    Uses caching to ensure consistent results for unchanged data.
    """
    print(f"News Agent: Analyzing for company {state['company_name']} ({state['company_id']})")

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
            return {"news_analysis": "No recent news found for this company."}

        # Collect chunks from these articles
        news_content = []
        for article in articles:
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

            news_content.append(f"Date: {article.published_at}\nTitle: {article.title}\nContent:\n{article_text}\n---")
            
        # [NEW] Semantic Search for extra context
        try:
            from app.services.embedding_service import embedding_service
            
            # Query for key risks and events
            query = f"Key risks, financial performance, major events, ESG controversies, greenwashing, labor disputes, governance scandals, deforestation for {state['company_name']}"
            query_vec = embedding_service.generate_embeddings([query])[0]
            
            vector_stmt = (
                select(NewsChunk)
                .join(NewsArticle)
                .where(NewsArticle.company_id == state["company_id"])
                .order_by(NewsChunk.embedding.l2_distance(query_vec))
                .limit(8)
            )
            
            relevant_chunks = session.exec(vector_stmt).all()
            
            if relevant_chunks:
                news_content.append("\n### Relevant Excerpts (Semantic Search):")
                for rc in relevant_chunks:
                    # Avoid duplicates if possible, or just append
                    news_content.append(f"- ...{rc.content}...")
                    
        except Exception as e:
            print(f"Vector search failed (ignoring): {e}")

    context = "\n".join(news_content)

    # Generate cache key based on content hash
    content_hash = hash_content(context)
    cache_key = generate_cache_key("news", state["company_id"], content_hash)

    # Check cache first
    cached_result = get_cached_result(cache_key)
    if cached_result:
        return {"news_analysis": cached_result}

    # Check token limit roughly (characters / 4)
    if len(context) > 25000:
        context = context[:25000] + "..."

    prompt = f"""You are a News Analyst. Analyze the following recent news articles for {state['company_name']}.
    Identify key events, market sentiment, and potential risks or opportunities.

    News Context:
    {context}

    Provide a concise summary analysis in Markdown."""

    llm = get_llm("llama-3.1-8b-instant")
    response = llm.invoke([SystemMessage(content="You are a helpful financial news analyst."), HumanMessage(content=prompt)])

    # Cache the result
    set_cached_result(cache_key, response.content)


    return {"news_analysis": response.content}

def news_critique(state: AgentState) -> Dict[str, Any]:
    """
    Critiques other agents' findings based on News data.
    """
    print(f"News Agent: Critiquing findings for {state['company_name']}")
    
    financial_analysis = state.get("financial_analysis", "No financial analysis provided.")
    claims_analysis = state.get("claims_analysis", "No claims analysis provided.")
    my_analysis = state.get("news_analysis", "No news analysis provided.")

    prompt = f"""You are a News Analyst. You have already provided your analysis.
    Now, review the findings from the Financial Analyst and the Claims (Documents) Analyst.
    
    Your Task:
    Critique their findings based *only* on the news signals you have.
    - If Financials say "Growth is up" but News says "Major layoffs", point out the discrepancy.
    - If Claims say "We are eco-friendly" but News deals with "Pollution Scandal", flag it.
    - Confirm agreement if news supports their claims.

    1. NEWS ANALYSIS (Your Context):
    {my_analysis}

    2. FINANCIAL ANALYSIS (To Critique):
    {financial_analysis}

    3. CLAIMS ANALYSIS (To Critique):
    {claims_analysis}

    Provide a concise critique (max 200 words) focusing on CONSISTENCY and CONTRADICTIONS.
    """

    llm = get_llm("llama-3.1-8b-instant")
    response = llm.invoke([SystemMessage(content="You are a critical news analyst."), HumanMessage(content=prompt)])
    
    return {"news_critique": response.content}
