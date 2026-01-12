"""
Script to regenerate summaries for news articles that have placeholder summaries.
Uses the existing AI service to generate proper summaries from article content or title.
"""
from sqlmodel import Session, select
import logging
import time

from app.database import engine
from app.models import NewsArticle
from app.ai_service import summarize_article

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLACEHOLDER = "Click title to read full article content."

def regenerate_summaries():
    """Regenerate summaries for articles with placeholder text."""
    with Session(engine) as session:
        # Find articles with placeholder summary
        query = select(NewsArticle).where(
            (NewsArticle.summary == PLACEHOLDER) |
            (NewsArticle.summary == None)
        )
        articles = session.exec(query).all()

        logger.info(f"Found {len(articles)} articles needing summary regeneration")

        for i, article in enumerate(articles):
            logger.info(f"[{i+1}/{len(articles)}] Processing: {article.title[:50]}...")

            # Use content if available and substantial, otherwise use title
            text_to_summarize = article.content if article.content and len(article.content) > 100 else article.title

            try:
                summary = summarize_article(text_to_summarize)

                if summary and not summary.startswith("Error"):
                    article.summary = summary
                    session.add(article)
                    session.commit()
                    logger.info(f"  ✓ Generated: {summary[:80]}...")
                else:
                    logger.warning(f"  ✗ Failed to generate summary: {summary}")

            except Exception as e:
                logger.error(f"  ✗ Error: {e}")

            # Rate limiting to avoid API throttling
            time.sleep(1)

        logger.info("Summary regeneration complete!")

if __name__ == "__main__":
    regenerate_summaries()
