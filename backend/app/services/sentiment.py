import os
import requests
from openai import OpenAI
from typing import Literal
import json

SentimentType = Literal["positive", "neutral", "negative"]

class SentimentService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
    
    def fetch_article_content(self, url: str, source: str) -> str:
        """
        Fetch the full content of an article from various sources.
        Falls back to using the provided description if fetching fails.
        """
        try:
            # For now, we'll use a simple fetch
            # In production, you might want more sophisticated scraping
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Timeout after 5 seconds
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                # Basic text extraction - you could use BeautifulSoup for better parsing
                text = response.text
                # Simple extraction - remove HTML tags roughly
                import re
                text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                
                # Limit to first 2000 characters for analysis
                return text[:2000]
        except Exception as e:
            print(f"Error fetching article content from {url}: {e}")
        
        return ""
    
    def analyze_sentiment(
        self, 
        title: str, 
        content: str, 
        company_name: str,
        description: str = ""
    ) -> dict:
        """
        Analyze the sentiment of a news article relative to the company.
        
        Returns:
            {
                "sentiment": "positive" | "neutral" | "negative",
                "confidence": float,
                "reasoning": str
            }
        """
        # Combine available text for analysis
        text_to_analyze = f"Title: {title}\n\n"
        if description:
            text_to_analyze += f"Summary: {description}\n\n"
        if content:
            text_to_analyze += f"Content: {content}"
        
        # Truncate if too long (Groq has token limits)
        text_to_analyze = text_to_analyze[:3000]
        
        prompt = f"""Analyze the sentiment of this news article about {company_name}.

Article:
{text_to_analyze}

Determine if this news is POSITIVE, NEUTRAL, or NEGATIVE for {company_name}'s business, reputation, and stock performance.

Respond ONLY with a JSON object in this exact format:
{{
    "sentiment": "positive" or "neutral" or "negative",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation in 1-2 sentences"
}}

Examples:
- Revenue growth, new contracts, partnerships → positive
- Regulatory approval, stable earnings → positive
- Routine announcements, general news → neutral
- Lawsuits, losses, scandals, negative earnings → negative"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial news sentiment analyst. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            # Remove markdown code blocks if present
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(result_text)
            
            # Validate response
            sentiment = result.get("sentiment", "neutral").lower()
            if sentiment not in ["positive", "neutral", "negative"]:
                sentiment = "neutral"
            
            confidence = float(result.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))
            
            reasoning = result.get("reasoning", "")
            
            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "reasoning": reasoning
            }
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {result_text}")
            print(f"Error: {e}")
            # Fallback: try to extract sentiment from text
            result_text_lower = result_text.lower()
            if "positive" in result_text_lower:
                return {"sentiment": "positive", "confidence": 0.6, "reasoning": "Extracted from response"}
            elif "negative" in result_text_lower:
                return {"sentiment": "negative", "confidence": 0.6, "reasoning": "Extracted from response"}
            else:
                return {"sentiment": "neutral", "confidence": 0.5, "reasoning": "Unable to determine"}
                
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "reasoning": f"Error: {str(e)}"
            }
    
    def analyze_batch(self, articles: list) -> dict:
        """
        Analyze sentiment for multiple articles.
        
        Args:
            articles: List of dicts with keys: id, title, content, company_name, description, url, source
        
        Returns:
            Dict mapping article IDs to sentiment results
        """
        results = {}
        
        for article in articles:
            article_id = article.get("id")
            title = article.get("title", "")
            description = article.get("description", "")
            company_name = article.get("company", "")
            url = article.get("url", "")
            source = article.get("source", "")
            
            # Try to fetch full content
            content = article.get("content", "")
            if not content and url:
                content = self.fetch_article_content(url, source)
            
            # Analyze sentiment
            sentiment_result = self.analyze_sentiment(
                title=title,
                content=content,
                company_name=company_name,
                description=description
            )
            
            results[article_id] = sentiment_result
        
        return results

sentiment_service = SentimentService()
