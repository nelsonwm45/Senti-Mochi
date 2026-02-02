"""
Sentiment Analysis Service using Groq LLM
Analyzes news articles and stores sentiment results in the database
"""
import json
import os
from typing import Optional, Dict, Tuple
import openai
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.models import NewsArticle, Company


class SentimentAnalyzer:
    """Analyzes sentiment of news articles using Groq"""
    
    def __init__(self):
        """Initialize Groq client (OpenAI-compatible)"""
        self.client = openai.OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = "llama-3.3-70b-versatile"
    
    def analyze_article(self, article: NewsArticle, company: Company) -> Optional[Dict]:
        """
        Analyze sentiment of a single article.
        
        Args:
            article: NewsArticle object to analyze
            company: Company object for context
            
        Returns:
            Dictionary with sentiment_label, sentiment_score, sentiment_confidence
            or None if analysis fails
        """
        # Skip if article has already been analyzed
        if article.analyzed_at is not None:
            return None
        
        # Skip Bursa Announcements
        if article.source.lower() == "bursa":
            return None
        
        # Skip if no content
        if not article.content or article.content.strip() == "":
            return None
        
        try:
            sentiment_data = self._call_llm(article, company)
            return sentiment_data
        except Exception as e:
            print(f"Error analyzing sentiment for article {article.id}: {e}")
            return None
    
    def _call_llm(self, article: NewsArticle, company: Company) -> Dict:
        """
        Call LLM (Cerebras with Groq fallback) to analyze sentiment.
        """
        from app.agents.base import get_llm
        from langchain_core.messages import SystemMessage, HumanMessage
        
        prompt = self._build_prompt(article, company)
        system_msg = "You are a financial sentiment analysis expert. Analyze news articles relative to their company and determine sentiment as Positive, Neutral, or Negative. Respond in JSON format only."

        # Attempt Primary: Cerebras
        try:
            print(f"[Sentiment Service] Attempting Cerebras (llama-3.3-70b)...")
            llm = get_llm("llama-3.3-70b")
            response = llm.invoke([
                SystemMessage(content=system_msg),
                HumanMessage(content=prompt)
            ])
            print(f"[Sentiment Service] SUCCESS: Processed by Cerebras")
            return self._parse_response(response.content)
        except Exception as e:
            print(f"[Sentiment Service] Cerebras failed: {e}. Fallback to Groq...")
            try:
                llm = get_llm("llama-3.3-70b-versatile") # Groq's 70b
                response = llm.invoke([
                    SystemMessage(content=system_msg),
                    HumanMessage(content=prompt)
                ])
                print(f"[Sentiment Service] SUCCESS: Processed by Groq")
                return self._parse_response(response.content)
            except Exception as e2:
                print(f"[Sentiment Service] Groq failed too: {e2}")
                # Return neutral if everything fails
                return {
                    "sentiment_label": "Neutral",
                    "sentiment_score": 0.0,
                    "sentiment_confidence": 0.5
                }
    
    def _build_prompt(self, article: NewsArticle, company: Company) -> str:
        """Build the prompt for the LLM"""
        # Limit content but allow more than before (Cerebras can handle it)
        # 5000 chars is plenty for a single article sentiment
        content_preview = article.content[:5000] + "..." if len(article.content) > 5000 else article.content
        
        return f"""
Analyze the following news article about {company.name} ({company.ticker}) in the {company.sector or 'finance'} sector.

Article Title: {article.title}
Published: {article.published_at.strftime('%Y-%m-%d') if article.published_at else 'Unknown'}
Source: {article.source.upper()}

Article Content (preview):
{content_preview}

Based on this article, determine the sentiment relative to the company {company.name}. Consider factors like:
- Impact on company reputation or stock performance
- Tone of the article
- Type of news (positive developments, challenges, neutral information)

Respond with ONLY a JSON object (no markdown, no extra text) in this format:
{{
    "sentiment_label": "Positive" or "Neutral" or "Negative",
    "sentiment_score": a float between -1.0 (most negative) and 1.0 (most positive),
    "sentiment_confidence": a float between 0.0 and 1.0 indicating confidence in the analysis,
    "reasoning": "brief explanation of the sentiment"
}}
"""
    
    def _parse_response(self, content: str) -> Dict:
        """
        Parse Groq response and extract sentiment data
        
        Returns:
            Dictionary with sentiment_label, sentiment_score, sentiment_confidence
        """
        try:
            # Try to find JSON in the response (in case there's extra text)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = content[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate required fields
            if "sentiment_label" not in data or "sentiment_score" not in data:
                raise ValueError("Missing required fields in response")
            
            # Normalize sentiment label
            label = data["sentiment_label"].strip().lower()
            if label not in ["positive", "neutral", "negative"]:
                raise ValueError(f"Invalid sentiment label: {label}")
            
            # Normalize to proper case
            label = label.capitalize()
            
            return {
                "sentiment_label": label,
                "sentiment_score": float(data.get("sentiment_score", 0.0)),
                "sentiment_confidence": float(data.get("sentiment_confidence", 0.8))
            }
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Error parsing Groq response: {e}")
            print(f"Response content: {content}")
            # Return neutral if parsing fails
            return {
                "sentiment_label": "Neutral",
                "sentiment_score": 0.0,
                "sentiment_confidence": 0.5
            }
    
    def analyze_and_store(self, article: NewsArticle, company: Company, session: Session) -> bool:
        """
        Analyze article sentiment and store results in database.
        
        Args:
            article: NewsArticle object
            company: Company object
            session: Database session
            
        Returns:
            True if analysis was performed and stored, False otherwise
        """
        # Skip if already analyzed
        if article.analyzed_at is not None:
            return False
        
        # Skip Bursa Announcements
        if article.source.lower() == "bursa":
            return False
        
        # Skip if no content
        if not article.content or article.content.strip() == "":
            return False
        
        try:
            sentiment_data = self.analyze_article(article, company)
            
            if sentiment_data is None:
                return False
            
            # Update article with sentiment data
            article.sentiment_label = sentiment_data["sentiment_label"]
            article.sentiment_score = sentiment_data["sentiment_score"]
            article.sentiment_confidence = sentiment_data["sentiment_confidence"]
            article.analyzed_at = datetime.now(timezone.utc)
            
            session.add(article)
            session.commit()
            
            print(f"Stored sentiment for article {article.id}: {sentiment_data['sentiment_label']} ({sentiment_data['sentiment_score']:.2f})")
            return True
        except Exception as e:
            print(f"Error in analyze_and_store: {e}")
            return False
    
    def analyze_unanalyzed_articles(self, session: Session, limit: Optional[int] = None) -> int:
        """
        Find and analyze all articles that haven't been analyzed yet.
        
        Args:
            session: Database session
            limit: Max number of articles to analyze (None for all)
            
        Returns:
            Number of articles analyzed
        """
        # Query for unanalyzed articles (excluding Bursa)
        stmt = select(NewsArticle, Company).join(Company).where(
            (NewsArticle.analyzed_at == None) &
            (NewsArticle.source != "bursa") &
            (NewsArticle.content != None)
        )
        
        if limit:
            stmt = stmt.limit(limit)
        
        results = session.exec(stmt).all()
        
        analyzed_count = 0
        for article, company in results:
            if self.analyze_and_store(article, company, session):
                analyzed_count += 1
        
        return analyzed_count


# Singleton instance
sentiment_analyzer = SentimentAnalyzer()
