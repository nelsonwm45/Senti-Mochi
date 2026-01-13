"""
Article content fetching service using newspaper3k
"""
from newspaper import Article
import time
from typing import Optional

class ArticleFetcherService:
    @staticmethod
    def fetch_article_content(url: str, timeout: int = 10) -> Optional[str]:
        """
        Fetch full article content from a URL using newspaper3k.
        
        Args:
            url: The article URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            Full article text, or None if fetch fails
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            # Return the full article text
            content = article.text
            
            if content and len(content.strip()) > 0:
                return content.strip()
            
            return None
            
        except Exception as e:
            print(f"[ARTICLE_FETCHER] Error fetching content from {url}: {e}")
            return None
    
    @staticmethod
    def fetch_article_with_metadata(url: str) -> dict:
        """
        Fetch article with additional metadata (title, authors, publish date, etc.)
        
        Returns:
            Dictionary with article data
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            # Try to extract publish date
            try:
                article.nlp()  # This enables keyword extraction and summarization
            except:
                pass  # NLP features are optional
            
            return {
                'text': article.text,
                'title': article.title,
                'authors': article.authors,
                'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                'top_image': article.top_image,
                'keywords': article.keywords if hasattr(article, 'keywords') else [],
                'summary': article.summary if hasattr(article, 'summary') else None
            }
            
        except Exception as e:
            print(f"[ARTICLE_FETCHER] Error fetching article with metadata from {url}: {e}")
            return None


# Singleton instance
article_fetcher_service = ArticleFetcherService()
