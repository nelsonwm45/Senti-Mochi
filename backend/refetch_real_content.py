"""
Script to fetch real article content by decoding Google News URLs.
"""
from sqlmodel import Session, select
import logging
import time
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import re

from app.database import engine
from app.models import NewsArticle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def decode_google_news_url(source_url: str) -> str:
    """Decode Google News URL using their redirect page."""
    try:
        # Extract the article ID from the URL
        # Format: https://news.google.com/rss/articles/XXXX
        if "news.google.com" not in source_url:
            return source_url

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        # Try to get the redirect
        session = requests.Session()

        # First, try the RSS article URL directly
        resp = session.get(source_url, headers=headers, timeout=15, allow_redirects=False)

        if resp.status_code in [301, 302, 303, 307, 308]:
            redirect_url = resp.headers.get('Location', '')
            if redirect_url and 'news.google' not in redirect_url:
                return redirect_url

        # Try with allow_redirects=True
        resp = session.get(source_url, headers=headers, timeout=15, allow_redirects=True)

        # Check final URL
        if 'news.google' not in resp.url:
            return resp.url

        # Parse the page for the actual article link
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Look for article links
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http') and 'news.google' not in href and 'google.com' not in href:
                if any(domain in href for domain in ['theedgemarkets', 'thestar', 'freemalaysiatoday', 'bernama', 'nst.com', 'reuters', 'bloomberg']):
                    return href

        # Look for data-n-au attribute (article URL)
        article_elem = soup.find(attrs={'data-n-au': True})
        if article_elem:
            return article_elem['data-n-au']

        return source_url
    except Exception as e:
        logger.warning(f"URL decode error: {e}")
        return source_url


def fetch_article_text(url: str) -> str:
    """Fetch article text using newspaper3k."""
    try:
        article = Article(url)
        article.download()
        article.parse()

        if article.text and len(article.text) > 100:
            return article.text

        # Fallback: try direct scraping
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()

        # Try article tag first
        article_tag = soup.find('article')
        if article_tag:
            paragraphs = article_tag.find_all('p')
        else:
            paragraphs = soup.find_all('p')

        text_parts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30]
        content = ' '.join(text_parts)

        return content if len(content) > 100 else ""

    except Exception as e:
        logger.warning(f"Fetch error for {url}: {e}")
        return ""


def refetch_content():
    """Re-fetch real content for all articles."""
    with Session(engine) as session:
        articles = session.exec(select(NewsArticle)).all()
        logger.info(f"Processing {len(articles)} articles")

        success = 0
        for i, article in enumerate(articles):
            logger.info(f"\n[{i+1}/{len(articles)}] {article.title[:50]}...")

            # Decode Google News URL
            real_url = decode_google_news_url(article.url)

            if real_url != article.url:
                logger.info(f"  Decoded: {real_url[:70]}...")
            else:
                logger.info(f"  Could not decode URL, trying original...")

            # Fetch content
            content = fetch_article_text(real_url)

            if content and len(content) > 100:
                article.content = content

                # Show first 50 words
                words = content.split()[:50]
                preview = ' '.join(words)
                logger.info(f"  ✓ Content (50 words): {preview}...")

                session.add(article)
                session.commit()
                success += 1
            else:
                logger.warning(f"  ✗ No content fetched")

            time.sleep(2)

        logger.info(f"\nDone! Updated {success}/{len(articles)} articles")


if __name__ == "__main__":
    refetch_content()
