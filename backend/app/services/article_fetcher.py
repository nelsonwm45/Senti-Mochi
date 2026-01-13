"""
Article content fetching service using newspaper3k
"""
from newspaper import Article, Config
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
            # Configure newspaper3k for better extraction
            config = Config()
            config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            config.request_timeout = timeout
            config.fetch_images = False
            config.memoize_articles = False
            
            article = Article(url, config=config)
            article.download()
            article.parse()
            
            # Return the full article text
            content = article.text
            
            # Filter out common navigation/footer text
            if content:
                # Remove common footer patterns
                lines = content.split('\n')
                filtered_lines = [line for line in lines if line.strip() and 
                                 line.strip().lower() not in ['what to read next', 'related articles', 
                                                               'read more', 'share this article']]
                content = '\n'.join(filtered_lines).strip()
            
            if content and len(content.strip()) > 50:  # Require at least 50 chars
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
            # Configure newspaper3k for better extraction
            config = Config()
            config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            config.fetch_images = False
            config.memoize_articles = False
            
            article = Article(url, config=config)
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
