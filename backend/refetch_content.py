"""
Script to re-fetch actual article content for existing news articles.
"""
from sqlmodel import Session, select
import logging
import time
import requests
from newspaper import Article

from app.database import engine
from app.models import NewsArticle
from app.ai_service import summarize_article

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def resolve_url(url: str) -> str:
    """Resolves potential redirects (especially Google News)."""
    try:
        if "news.google.com" not in url:
            return url
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        return response.url
    except:
        return url


def fetch_article_content(url: str) -> str:
    """Uses newspaper3k to extract main article text."""
    try:
        final_url = resolve_url(url)
        logger.info(f"Resolved to: {final_url[:60]}...")

        article = Article(final_url)
        article.download()
        article.parse()

        text = article.text
        if len(text) < 100:
            meta = article.meta_description
            if meta and len(meta) > 50:
                return meta
            return ""

        return text
    except Exception as e:
        logger.warning(f"Extraction failed: {e}")
        return ""


def refetch_content():
    """Re-fetch content for articles with short/missing content."""
    with Session(engine) as session:
        articles = session.exec(select(NewsArticle)).all()

        logger.info(f"Found {len(articles)} articles to process")

        for i, article in enumerate(articles):
            # Skip if content is already substantial
            if article.content and len(article.content) > 300:
                logger.info(f"[{i+1}] Skipping (has content): {article.title[:40]}...")
                continue

            logger.info(f"[{i+1}/{len(articles)}] Fetching: {article.title[:40]}...")

            content = fetch_article_content(article.url)

            if content and len(content) > 100:
                article.content = content

                # Print first 50 words
                words = content.split()[:50]
                preview = ' '.join(words)
                logger.info(f"  Content preview (first 50 words): {preview}...")

                # Also regenerate summary if needed
                if not article.summary or article.summary == "Click title to read full article content.":
                    logger.info("  Regenerating summary...")
                    article.summary = summarize_article(content)

                session.add(article)
                session.commit()
                logger.info(f"  ✓ Updated content ({len(content)} chars)")
            else:
                logger.warning(f"  ✗ Could not fetch content")

            time.sleep(2)  # Rate limiting

        logger.info("Content refetch complete!")


if __name__ == "__main__":
    refetch_content()
