from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.sentiment import sentiment_service

router = APIRouter(prefix="/sentiment", tags=["sentiment"])

class ArticleInput(BaseModel):
    id: str
    title: str
    company: str
    description: Optional[str] = ""
    content: Optional[str] = ""
    url: Optional[str] = ""
    source: Optional[str] = ""

class SentimentRequest(BaseModel):
    articles: List[ArticleInput]

class SentimentResult(BaseModel):
    sentiment: str
    confidence: float
    reasoning: str

@router.post("/analyze", response_model=dict[str, SentimentResult])
def analyze_sentiment(request: SentimentRequest):
    """
    Analyze sentiment for multiple news articles using Groq LLM.
    
    Returns a mapping of article IDs to sentiment results.
    """
    try:
        articles = [article.dict() for article in request.articles]
        results = sentiment_service.analyze_batch(articles)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")

@router.post("/analyze-single")
def analyze_single_sentiment(article: ArticleInput):
    """
    Analyze sentiment for a single news article.
    """
    try:
        # Fetch content if URL provided
        content = article.content or ""
        if not content and article.url:
            content = sentiment_service.fetch_article_content(article.url, article.source or "")
        
        result = sentiment_service.analyze_sentiment(
            title=article.title,
            content=content,
            company_name=article.company,
            description=article.description or ""
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")
