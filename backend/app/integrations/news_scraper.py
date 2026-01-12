import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from datetime import datetime
import hashlib

class NewsScraper:
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.logger = logging.getLogger(f"scraper.{source_name}")
        self.headers = {
             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scrape(self) -> List[Dict]:
        """
        Main entry point to scrape latest news.
        Returns a list of dictionaries with keys: title, url, content, published_at
        """
        raise NotImplementedError("Subclasses must implement scrape()")

    def _generate_id(self, url: str) -> str:
        """Generate a unique ID (hash) from the URL for deduplication"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()

class TheEdgeScraper(NewsScraper):
    def __init__(self):
        super().__init__("Google News (Malaysia)", "https://news.google.com/rss/search?q=Malaysia+Stock+Market+Business&hl=en-MY&gl=MY&ceid=MY:en")

    def scrape(self) -> List[Dict]:
        self.logger.info("Fetching Google News RSS...")
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'xml')
            
            articles = []
            for item in soup.find_all('item'):
                title = item.title.text
                link = item.link.text
                pub_date_str = item.pubDate.text
                description = item.description.text if item.description else ""
                
                # Parse Date (e.g., "Mon, 12 Jan 2026 08:00:00 GMT")
                try:
                    pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
                except:
                    pub_date = datetime.now()

                # Deduplicate
                if any(a['url'] == link for a in articles):
                    continue

                if title:
                    articles.append({
                        "id": self._generate_id(link),
                        "source": "Google News", # Or parse source from title if available
                        "title": title,
                        "url": link,
                        "published_at": pub_date,
                        "content": title,
                        "description": description # Pass raw description
                    })
                
                if len(articles) >= 15:
                    break
            
            self.logger.info(f"Scraped {len(articles)} articles from RSS.")
            return articles

        except Exception as e:
            self.logger.error(f"Error scraping RSS: {e}")
            return []

class TheStarScraper(NewsScraper):
    def __init__(self):
        super().__init__("The Star", "https://www.thestar.com.my/rss/Business")

    def scrape(self) -> List[Dict]:
        self.logger.info("Scraping The Star RSS...")
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'xml')

            articles = []
            for item in soup.find_all('item')[:15]:
                title = item.title.text if item.title else ""
                link = item.link.text if item.link else ""
                pub_date_str = item.pubDate.text if item.pubDate else ""
                description = item.description.text if item.description else ""

                # Clean description (remove HTML)
                if description:
                    desc_soup = BeautifulSoup(description, 'html.parser')
                    description = desc_soup.get_text(strip=True)

                # Parse Date
                try:
                    pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                except:
                    pub_date = datetime.now()

                if title and link:
                    articles.append({
                        "id": self._generate_id(link),
                        "source": "The Star",
                        "title": title,
                        "url": link,
                        "published_at": pub_date,
                        "content": description,  # Use description as content
                        "description": description
                    })

            self.logger.info(f"Scraped {len(articles)} articles from The Star.")
            return articles

        except Exception as e:
            self.logger.error(f"Error scraping The Star: {e}")
            return []


class FMTScraper(NewsScraper):
    """Free Malaysia Today scraper"""
    def __init__(self):
        super().__init__("Free Malaysia Today", "https://www.freemalaysiatoday.com/category/business/feed/")

    def scrape(self) -> List[Dict]:
        self.logger.info("Scraping Free Malaysia Today RSS...")
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'xml')

            articles = []
            for item in soup.find_all('item')[:15]:
                title = item.title.text if item.title else ""
                link = item.link.text if item.link else ""
                pub_date_str = item.pubDate.text if item.pubDate else ""

                # Get content from content:encoded or description
                content_tag = item.find('content:encoded')
                if content_tag:
                    content_html = content_tag.text
                    content_soup = BeautifulSoup(content_html, 'html.parser')
                    content = content_soup.get_text(strip=True)
                else:
                    description = item.description.text if item.description else ""
                    desc_soup = BeautifulSoup(description, 'html.parser')
                    content = desc_soup.get_text(strip=True)

                # Parse Date
                try:
                    pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                except:
                    pub_date = datetime.now()

                if title and link and content:
                    articles.append({
                        "id": self._generate_id(link),
                        "source": "FMT",
                        "title": title,
                        "url": link,
                        "published_at": pub_date,
                        "content": content,
                        "description": content[:500]
                    })

            self.logger.info(f"Scraped {len(articles)} articles from FMT.")
            return articles

        except Exception as e:
            self.logger.error(f"Error scraping FMT: {e}")
            return []
