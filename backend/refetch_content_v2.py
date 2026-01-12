"""
Script to re-fetch actual article content using direct scraping.
"""
from sqlmodel import Session, select
import logging
import time
import requests
from bs4 import BeautifulSoup
import base64
import re

from app.database import engine
from app.models import NewsArticle
from app.ai_service import summarize_article

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def decode_google_news_url(url: str) -> str:
    """Attempt to decode Google News redirect URL."""
    try:
        # Try to follow the redirect with a browser-like request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15, allow_redirects=True)

        # Check if we got redirected to the actual article
        if "news.google.com" not in response.url:
            return response.url

        # Try to find redirect in the HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for meta refresh or JS redirect
        meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
        if meta_refresh:
            content = meta_refresh.get('content', '')
            match = re.search(r'url=(.+)', content, re.IGNORECASE)
            if match:
                return match.group(1)

        # Look for data-url attributes
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http') and 'news.google' not in href:
                return href

        return url
    except Exception as e:
        logger.warning(f"URL decode failed: {e}")
        return url


def fetch_content_from_url(url: str) -> str:
    """Fetch article content directly."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            tag.decompose()

        # Try to find article content
        article = soup.find('article')
        if article:
            paragraphs = article.find_all('p')
        else:
            paragraphs = soup.find_all('p')

        # Extract text from paragraphs
        text_parts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 50:  # Filter out short snippets
                text_parts.append(text)

        content = ' '.join(text_parts)
        return content if len(content) > 200 else ""

    except Exception as e:
        logger.warning(f"Content fetch failed: {e}")
        return ""


def refetch_content():
    """Re-fetch content for articles."""
    with Session(engine) as session:
        articles = session.exec(select(NewsArticle)).all()
        logger.info(f"Found {len(articles)} articles to process")

        success_count = 0
        for i, article in enumerate(articles):
            if article.content and len(article.content) > 300:
                logger.info(f"[{i+1}] Skipping (has content): {article.title[:40]}...")
                continue

            logger.info(f"[{i+1}/{len(articles)}] Processing: {article.title[:40]}...")

            # Try to decode Google News URL
            real_url = decode_google_news_url(article.url)
            logger.info(f"  URL: {real_url[:60]}...")

            # Fetch content
            content = fetch_content_from_url(real_url)

            if content and len(content) > 200:
                article.content = content

                # Print first 50 words
                words = content.split()[:50]
                preview = ' '.join(words)
                logger.info(f"  Content (first 50 words): {preview}...")

                # Regenerate summary
                if not article.summary or article.summary == "Click title to read full article content.":
                    logger.info("  Regenerating summary...")
                    article.summary = summarize_article(content)

                session.add(article)
                session.commit()
                success_count += 1
                logger.info(f"  ✓ Updated ({len(content)} chars)")
            else:
                logger.warning(f"  ✗ Could not fetch content")

            time.sleep(1)

        logger.info(f"Done! Updated {success_count}/{len(articles)} articles")


if __name__ == "__main__":
    refetch_content()
