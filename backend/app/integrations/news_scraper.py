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
        super().__init__("The Edge Markets", "https://theedgemalaysia.com")

    def scrape(self) -> List[Dict]:
        self.logger.info("Scraping The Edge...")
        # Simulated scraping logic
        # In reality: response = requests.get(self.base_url, headers=self.headers)
        # soup = BeautifulSoup(response.text, 'lxml')
        # ... parse logic
        
        # Returning mock data for MVP
        return [
            {
                "id": self._generate_id("https://theedgemalaysia.com/article/mock-1"),
                "source": self.source_name,
                "title": "Bursa Malaysia closes higher on strong buying support",
                "url": "https://theedgemalaysia.com/article/mock-1",
                "published_at": datetime.now(),
                "content": "KUALA LUMPUR (Jan 12): Bursa Malaysia ended the trading week on a positive note..."
            },
            {
                "id": self._generate_id("https://theedgemalaysia.com/article/mock-2"),
                "source": self.source_name,
                "title": "Maybank records higher net profit in Q4",
                "url": "https://theedgemalaysia.com/article/mock-2",
                "published_at": datetime.now(),
                "content": "Malayan Banking Bhd (Maybank) posted a net profit of..."
            }
        ]

class TheStarScraper(NewsScraper):
    def __init__(self):
        super().__init__("The Star", "https://www.thestar.com.my/business")

    def scrape(self) -> List[Dict]:
        self.logger.info("Scraping The Star...")
        return []
