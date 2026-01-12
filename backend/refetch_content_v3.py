"""
Script to re-fetch article content using gnews library to decode Google News URLs.
"""
from sqlmodel import Session, select
import logging
import time
import requests
from bs4 import BeautifulSoup
from newspaper import Article

from app.database import engine
from app.models import NewsArticle
from app.ai_service import summarize_article

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google News URL decoder
try:
    from gnews.utils.utils import decode_google_news_url
    HAS_GNEWS = True
except ImportError:
    HAS_GNEWS = False
    logger.warning("gnews not available")


def get_real_url(google_news_url: str) -> str:
    """Decode Google News URL to get actual article URL."""
    if "news.google.com" not in google_news_url:
        return google_news_url

    if HAS_GNEWS:
        try:
            decoded = decode_google_news_url(google_news_url)
            if decoded:
                return decoded
        except Exception as e:
            logger.warning(f"gnews decode failed: {e}")

    return google_news_url


def fetch_article_content(url: str) -> str:
    """Fetch article content using newspaper3k."""
    try:
        article = Article(url)
        article.download()
        article.parse()

        text = article.text
        if len(text) > 200:
            return text

        # Fallback to meta description
        if article.meta_description and len(article.meta_description) > 50:
            return article.meta_description

        return ""
    except Exception as e:
        logger.warning(f"Article fetch failed: {e}")
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

            # Decode Google News URL
            real_url = get_real_url(article.url)
            if real_url != article.url:
                logger.info(f"  Decoded URL: {real_url[:60]}...")
            else:
                logger.info(f"  Could not decode, using original URL")

            # Fetch content
            content = fetch_article_content(real_url)

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

            time.sleep(2)

        logger.info(f"Done! Updated {success_count}/{len(articles)} articles")


if __name__ == "__main__":
    refetch_content()
