"""
Article content fetching service using newspaper3k and Scrapy for NST articles
"""
from newspaper import Article, Config
import time
from typing import Optional
import re
import json
from urllib.parse import urlparse

class ArticleFetcherService:
    @staticmethod
    def _is_nst_article(url: str) -> bool:
        """Check if URL is from NST (New Straits Times)"""
        parsed = urlparse(url)
        return 'nst.com.my' in parsed.netloc
    
    @staticmethod
    def _fetch_nst_article(url: str) -> Optional[str]:
        """Fetch NST article using custom scraping (newspaper3k doesn't work for NST)"""
        try:
            import requests
            from html import unescape
            
            print(f"[NST_SCRAPER] Fetching URL: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            html_content = response.text
            
            print(f"[NST_SCRAPER] Received {len(html_content)} chars of HTML")
            
            # NST uses Vue.js components with JSON data embedded in the page
            # Try multiple regex patterns to handle different HTML structures
            article_json_raw = None
            
            # Pattern 1: Standard with &quot; (with DOTALL to handle newlines)
            match = re.search(r'<article-component\s+:article=&quot;(.+?)&quot;', html_content, re.DOTALL)
            if match:
                article_json_raw = match.group(1)
                print(f"[NST_SCRAPER] Found article-component using pattern 1")
            
            # Pattern 2: With regular quotes
            if not article_json_raw:
                match = re.search(r'<article-component\s+:article="([^"]+)"', html_content, re.DOTALL)
                if match:
                    article_json_raw = match.group(1)
                    print(f"[NST_SCRAPER] Found article-component using pattern 2")
            
            # Pattern 3: Try to find just the body field
            if not article_json_raw:
                match = re.search(r'"body":"((?:[^"\\]|\\.)*?)"', html_content)
                if match:
                    article_json_raw = '{"body":"' + match.group(1) + '"}'
                    print(f"[NST_SCRAPER] Found body field using pattern 3")
            
            if not article_json_raw:
                print(f"[NST_SCRAPER] Could not find article-component in HTML")
                return None
            
            try:
                article_json_raw = unescape(article_json_raw)
                article_data = json.loads(article_json_raw)
                body_html = article_data.get('body', '')
            except (json.JSONDecodeError, ValueError) as je:
                print(f"[NST_SCRAPER] JSON decode error: {je}, trying manual body extraction...")
                # Try to find the body field manually
                body_match = re.search(r'"body":"((?:[^"\\]|\\.)*?)"', article_json_raw)
                if body_match:
                    body_html = body_match.group(1)
                    body_html = unescape(body_html)
                else:
                    return None
            
            if body_html:
                print(f"[NST_SCRAPER] Found body HTML with {len(body_html)} chars")
                # Remove HTML tags
                text = re.sub(r'<[^>]+>', '', body_html)
                # Decode HTML entities
                text = unescape(text)
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                # Split into paragraphs and rejoin
                paragraphs = [p.strip() for p in text.split('  ') if p.strip()]
                content = '\n\n'.join(paragraphs)
                
                if content and len(content) > 50:
                    print(f"[NST_SCRAPER] Successfully extracted {len(content)} chars of content")
                    return content
            else:
                print(f"[NST_SCRAPER] No body HTML found in JSON data")
            
            return None
            
        except Exception as e:
            print(f"[ARTICLE_FETCHER] Error fetching NST article from {url}: {e}")
            return None
    
    @staticmethod
    def fetch_article_content(url: str, timeout: int = 10) -> Optional[str]:
        """
        Fetch full article content from a URL.
        Uses custom scraper for NST articles, newspaper3k for others.
        
        Args:
            url: The article URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            Full article text, or None if fetch fails
        """
        # Check if this is an NST article
        if ArticleFetcherService._is_nst_article(url):
            print(f"[ARTICLE_FETCHER] Detected NST article, using custom scraper")
            content = ArticleFetcherService._fetch_nst_article(url)
            if content:
                return content
            print(f"[ARTICLE_FETCHER] NST scraper failed, falling back to newspaper3k")
        
        # Use newspaper3k for other sites or as fallback
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
        # Check if this is an NST article
        if ArticleFetcherService._is_nst_article(url):
            try:
                import requests
                from html import unescape
                from datetime import datetime
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                html_content = response.text
                
                article_component_match = re.search(r'<article-component\s+:article=&quot;(.+?)&quot;', html_content)
                
                if article_component_match:
                    article_json_raw = article_component_match.group(1)
                    article_json_raw = unescape(article_json_raw)
                    article_data = json.loads(article_json_raw)
                    
                    # Extract body HTML and convert to plain text
                    body_html = article_data.get('body', '')
                    text = re.sub(r'<[^>]+>', '', body_html)
                    text = unescape(text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    # Extract metadata
                    title = article_data.get('title', '')
                    author_data = article_data.get('field_article_author', {})
                    author = author_data.get('name') if author_data else None
                    
                    # Extract publication date
                    created_timestamp = article_data.get('created')
                    pub_date = datetime.fromtimestamp(created_timestamp).isoformat() if created_timestamp else None
                    
                    # Extract tags
                    tags_data = article_data.get('field_tags', [])
                    keywords = [tag.get('name') for tag in tags_data if tag.get('name')]
                    
                    # Extract image
                    images_data = article_data.get('field_article_images', [])
                    top_image = images_data[0].get('url') if images_data else None
                    
                    return {
                        'text': text,
                        'title': title,
                        'authors': [author] if author else [],
                        'publish_date': pub_date,
                        'top_image': top_image,
                        'keywords': keywords,
                        'summary': article_data.get('field_article_lead')
                    }
            except Exception as e:
                print(f"[ARTICLE_FETCHER] NST metadata extraction failed, falling back to newspaper3k: {e}")
        
        # Use newspaper3k for other sites or as fallback
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
