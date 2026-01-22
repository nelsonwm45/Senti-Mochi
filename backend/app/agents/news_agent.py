
from typing import Dict, Any
from sqlmodel import Session, select, col
from app.database import engine
from app.models import NewsArticle, NewsChunk, Company
from app.agents.base import get_llm
from app.agents.state import AgentState
from langchain_core.messages import SystemMessage, HumanMessage

def news_agent(state: AgentState) -> Dict[str, Any]:
    """
    Fetches recent news and generates an analysis.
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
            # We can fetch chunks or just use content if chunks not fully populated yet
            # But the requirement is to use chunks. 
            # Let's try to fetch chunks first.
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
            
    context = "\n".join(news_content)
    
    # Check token limit roughly (characters / 4)
    # If too long, truncate? Llama 3-70b supports 8k context.
    if len(context) > 25000: # ~6k tokens
        context = context[:25000] + "..."
        
    prompt = f"""You are a News Analyst. Analyze the following recent news articles for {state['company_name']}.
    Identify key events, market sentiment, and potential risks or opportunities.
    
    News Context:
    {context}
    
    Provide a concise summary analysis in Markdown."""
    
    llm = get_llm("llama-3.3-70b-versatile")
    response = llm.invoke([SystemMessage(content="You are a helpful financial news analyst."), HumanMessage(content=prompt)])
    
    return {"news_analysis": response.content}
