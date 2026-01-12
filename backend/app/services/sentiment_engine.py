from uuid import UUID
from sqlmodel import Session, select
from app.database import engine
from app.models import SentimentAnalysis, NewsArticle, Filing
from app.ai_service import analyze_financial_sentiment
import logging

logger = logging.getLogger(__name__)

class SentimentEngine:
    def process_news(self, article_id: UUID):
        with Session(engine) as session:
            article = session.get(NewsArticle, article_id)
            if not article:
                logger.error(f"Article {article_id} not found")
                return
            
            # Analyze
            result = analyze_financial_sentiment(article.content)
            
            # Save
            sentiment = SentimentAnalysis(
                news_article_id=article.id,
                score=result.get("score", "Neutral"),
                confidence_score=result.get("confidence", 0.0),
                rationale=result.get("rationale", "")
            )
            session.add(sentiment)
            
            # Optionally update denormalized score on Article
            # article.sentiment_score = ... (if mapped to float)
            
            session.commit()
            logger.info(f"Sentiment for article {article_id}: {sentiment.score}")

    def process_filing(self, filing_id: UUID):
        with Session(engine) as session:
            filing = session.get(Filing, filing_id)
            if not filing:
                return

            if not filing.content_summary:
                # Need content summary or full text. 
                # For MVP, assume content_summary is populated by Processor
                logger.warning(f"Filing {filing_id} has no summary to analyze")
                return

            result = analyze_financial_sentiment(filing.content_summary)
            
            sentiment = SentimentAnalysis(
                filing_id=filing.id,
                score=result.get("score", "Neutral"),
                confidence_score=result.get("confidence", 0.0),
                rationale=result.get("rationale", "")
            )
            session.add(sentiment)
            session.commit()
