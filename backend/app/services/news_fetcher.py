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
                    created = item.get('created')
                    
                    if not nid:
                        continue
                    
                    # Convert created timestamp to ISO format
                    if created:
                        try:
                            published_at = datetime.fromtimestamp(created).isoformat()
                        except:
                            published_at = datetime.now().isoformat()
                    else:
                        published_at = datetime.now().isoformat()
                    
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
