"""
Service for fetching news from various sources (Star, NST, etc.) via backend.
This allows searching for specific keywords across news sources.
"""
import requests
from typing import List, Optional
from datetime import datetime
from urllib.parse import quote
import json
import re
from app.models import Company

class NewsFetcherService:
    """Service to fetch news articles from various sources by keyword."""
    
    @staticmethod
    def fetch_star_news(keyword: str) -> List[dict]:
        """
        Fetch news from The Star by keyword.
        
        Args:
            keyword: Search keyword (e.g., "Maybank", "Top Glove")
            
        Returns:
            List of article dictionaries with source='star'
        """
        articles = []
        
        try:
            query = quote(keyword)
            url = f"https://api.queryly.com/json.aspx?queryly_key=6ddd278bf17648ac&query={query}&endindex=0&batchsize=5&showfaceted=true&extendeddatafields=paywalltype,isexclusive,kicker,kickerurl,summary,sponsor&timezoneoffset=-450"
            
            print(f"[STAR_NEWS] Fetching for keyword: {keyword}")
            
            response = requests.get(url, headers={'Accept': 'application/json'}, timeout=10)
            
            if not response.ok:
                print(f"[STAR_NEWS] Request failed with status {response.status_code}")
                return articles
            
            text = response.text
            data = None
            
            # Handle JSONP response
            if 'resultcallback' in text:
                match_obj = re.search(r'resultcallback\s*\(\s*({[\s\S]*})\s*\)', text)
                if match_obj:
                    data = json.loads(match_obj.group(1))
            else:
                data = response.json()
            
            if not data:
                print(f"[STAR_NEWS] Could not parse response")
                return articles
            
            items = data.get('items', [])
            print(f"[STAR_NEWS] Found {len(items)} items")
            
            for item in items[:5]:  # Limit to 5 items
                try:
                    published_at = datetime.fromtimestamp(item.get('pubdateunix', 0)).isoformat()
                    
                    article = {
                        'source': 'star',
                        'native_id': f"star-{item.get('_id')}",
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'published_at': published_at,
                        'content': item.get('title', '')  # Backend will enrich with full content
                    }
                    articles.append(article)
                except Exception as e:
                    print(f"[STAR_NEWS] Error parsing item: {e}")
                    continue
            
            print(f"[STAR_NEWS] Successfully fetched {len(articles)} articles")
            return articles
            
        except Exception as e:
            print(f"[STAR_NEWS] Error fetching news: {e}")
            return articles
    
    @staticmethod
    def fetch_nst_news(keyword: str) -> List[dict]:
        """
        Fetch news from New Straits Times (NST) by keyword.
        
        Args:
            keyword: Search keyword (e.g., "Maybank", "Top Glove")
            
        Returns:
            List of article dictionaries with source='nst'
        """
        articles = []
        
        try:
            # NST API endpoint
            query = quote(keyword)
            # Using the format from the frontend
            url = f"https://www.nst.com.my/api/search?keywords={query}&category=&sort=DESC&page_size=5&page=0"
            
            print(f"[NST_NEWS] Fetching for keyword: {keyword}")
            
            response = requests.get(url, headers={'Accept': 'application/json'}, timeout=10)
            
            if not response.ok:
                print(f"[NST_NEWS] Request failed with status {response.status_code}")
                return articles
            
            data = response.json()
            items = data.get('data', [])
            
            print(f"[NST_NEWS] Found {len(items)} items")
            
            for item in items[:5]:  # Limit to 5 items
                try:
                    published_at = datetime.fromtimestamp(item.get('created', 0)).isoformat()
                    
                    article = {
                        'source': 'nst',
                        'native_id': f"nst-{item.get('nid')}",
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'published_at': published_at,
                        'content': item.get('title', '')  # Backend will enrich with full content
                    }
                    articles.append(article)
                except Exception as e:
                    print(f"[NST_NEWS] Error parsing item: {e}")
                    continue
            
            print(f"[NST_NEWS] Successfully fetched {len(articles)} articles")
            return articles
            
        except Exception as e:
            print(f"[NST_NEWS] Error fetching news: {e}")
            return articles
    
    @staticmethod
    def fetch_edge_news(keyword: str) -> List[dict]:
        """
        Fetch news from The Edge (theedgemalaysia.com) by keyword.
        
        Args:
            keyword: Search keyword (e.g., "Maybank", "Top Glove")
            
        Returns:
            List of article dictionaries with source='edge'
        """
        articles = []
        
        try:
            query = quote(keyword)
            # The Edge search URL with parameters
            url = (
                f"https://theedgemalaysia.com/news-search-results?"
                f"keywords={query}"
                f"&to=2026-01-21"
                f"&from=1999-01-01"
                f"&language=english"
                f"&offset=0"
            )
            
            print(f"[EDGE_NEWS] Fetching for keyword: {keyword}")
            
            response = requests.get(url, headers={'Accept': 'application/json'}, timeout=10)
            
            if not response.ok:
                print(f"[EDGE_NEWS] Request failed with status {response.status_code}")
                return articles
            
            print(f"[EDGE_NEWS] Got response, checking for __NEXT_DATA__")
            
            # Extract JSON from __NEXT_DATA__ script tag
            pattern = r'<script id="__NEXT_DATA__" type="application/json">\s*(\{[\s\S]*?\})\s*</script>'
            match = re.search(pattern, response.text)
            
            if not match:
                print(f"[EDGE_NEWS] Could not find __NEXT_DATA__ in HTML")
                return articles
            
            try:
                json_string = match.group(1)
                data = json.loads(json_string)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"[EDGE_NEWS] Error parsing JSON: {e}")
                return articles
            
            # Extract articles from nested structure
            articles_data = data.get('props', {}).get('pageProps', {}).get('newsArticleData', [])
            
            if not articles_data:
                print(f"[EDGE_NEWS] No articles found in parsed data")
                return articles
            
            print(f"[EDGE_NEWS] Found {len(articles_data)} articles")
            
            for item in articles_data[:5]:  # Limit to 5 items
                try:
                    nid = item.get('nid')
                    title = item.get('title', '')
                    author = item.get('author', '')
                    
                    if not nid:
                        continue
                    
                    print(f"[EDGE_NEWS] Processing article: {title[:50]}")
                    print(f"[EDGE_NEWS] Available fields: {list(item.keys())}")
                    
                    # Try multiple date fields (created, timestamp, date, published, etc.)
                    published_at = None
                    for date_field in ['created', 'updated', 'timestamp', 'date', 'published', 'publish_date', 'pubdate', 'changed']:
                        date_value = item.get(date_field)
                        if date_value:
                            try:
                                # Handle both milliseconds and seconds timestamps
                                timestamp = float(date_value)
                                # If timestamp is larger than year 2200 in seconds, it's in milliseconds
                                if timestamp > 7258118400:
                                    timestamp = timestamp / 1000
                                
                                published_at = datetime.fromtimestamp(timestamp).isoformat()
                                print(f"[EDGE_NEWS] Found date in '{date_field}': {published_at}")
                                break
                            except:
                                # Try as ISO string
                                try:
                                    published_at = datetime.fromisoformat(str(date_value).replace('Z', '+00:00')).isoformat()
                                    print(f"[EDGE_NEWS] Parsed ISO date from '{date_field}': {published_at}")
                                    break
                                except:
                                    continue
                    
                    # If no date found in JSON, try fetching from article page
                    if not published_at:
                        article_url = f"https://theedgemalaysia.com/node/{nid}"
                        try:
                            print(f"[EDGE_NEWS] No date in JSON, fetching article page: {article_url}")
                            article_response = requests.get(article_url, timeout=5)
                            if article_response.ok:
                                # Look for date in meta tags or article HTML
                                date_patterns = [
                                    r'<meta property="article:published_time" content="([^"]+)"',
                                    r'<meta property="datePublished" content="([^"]+)"',
                                    r'<time datetime="([^"]+)"',
                                    r'"datePublished":"([^"]+)"',
                                    r'"publishedDate":"([^"]+)"',
                                    r'<span class="date[^>]*>([^<]+)</span>',
                                    r'<span[^>]*class="[^"]*published[^"]*"[^>]*>([^<]+)</span>'
                                ]
                                
                                for pattern in date_patterns:
                                    match = re.search(pattern, article_response.text)
                                    if match:
                                        try:
                                            date_str = match.group(1)
                                            published_at = datetime.fromisoformat(date_str.replace('Z', '+00:00')).isoformat()
                                            print(f"[EDGE_NEWS] Extracted date from HTML: {published_at}")
                                            break
                                        except Exception as parse_err:
                                            print(f"[EDGE_NEWS] Could not parse date string '{date_str}': {parse_err}")
                                            continue
                        except Exception as e:
                            print(f"[EDGE_NEWS] Error fetching article page for date: {e}")
                    
                    # Fallback to current time if still no date
                    if not published_at:
                        published_at = datetime.now().isoformat()
                        print(f"[EDGE_NEWS] Using current time as fallback")
                    
                    # Construct article URL
                    article_url = f"https://theedgemalaysia.com/node/{nid}"
                    
                    article = {
                        'source': 'edge',
                        'native_id': f"edge-{nid}",
                        'title': title,
                        'url': article_url,
                        'published_at': published_at,
                        'content': title,  # Will be enriched with full content by backend
                        'author': author
                    }
                    articles.append(article)
                except Exception as e:
                    print(f"[EDGE_NEWS] Error parsing article item: {e}")
                    continue
            
            print(f"[EDGE_NEWS] Successfully fetched {len(articles)} articles")
            return articles
            
        except Exception as e:
            print(f"[EDGE_NEWS] Error fetching news: {e}")
            return articles
    
    @staticmethod
    def fetch_news_by_company(company: Company, sources: Optional[List[str]] = None) -> dict:
        """
        Fetch news for a specific company using its common_name (layman's name).
        
        Args:
            company: Company object with common_name and ticker
            sources: List of sources to fetch from (default: ['star', 'nst', 'edge'])
            
        Returns:
            Dictionary with articles grouped by source
        """
        # Use common_name if available (e.g., "Maybank"), fallback to ticker
        search_keyword = company.common_name or company.name or company.ticker
        print(f"[NEWS_FETCHER] Fetching news for {company.name} ({company.ticker}) using keyword: {search_keyword}")
        return NewsFetcherService.fetch_news_by_keyword(search_keyword, sources)
    
    @staticmethod
    def fetch_news_by_keyword(keyword: str, sources: Optional[List[str]] = None) -> dict:
        """
        Fetch news from multiple sources by keyword.
        
        Args:
            keyword: Search keyword (e.g., "Maybank", "Top Glove ESG")
            sources: List of sources to fetch from (default: ['star', 'nst', 'edge'])
            
        Returns:
            Dictionary with articles grouped by source:
            {
                'star': [article_dict, ...],
                'nst': [article_dict, ...],
                'edge': [article_dict, ...],
                'total': int
            }
        """
        if sources is None:
            sources = ['star', 'nst', 'edge']
        
        result = {'total': 0}
        
        # Fetch from Star
        if 'star' in sources:
            star_articles = NewsFetcherService.fetch_star_news(keyword)
            result['star'] = star_articles
            result['total'] += len(star_articles)
        
        # Fetch from NST
        if 'nst' in sources:
            nst_articles = NewsFetcherService.fetch_nst_news(keyword)
            result['nst'] = nst_articles
            result['total'] += len(nst_articles)
        
        # Fetch from The Edge
        if 'edge' in sources:
            edge_articles = NewsFetcherService.fetch_edge_news(keyword)
            result['edge'] = edge_articles
            result['total'] += len(edge_articles)
        
        print(f"[NEWS_FETCHER] Total articles fetched: {result['total']}")
        return result


# Singleton instance
news_fetcher_service = NewsFetcherService()
