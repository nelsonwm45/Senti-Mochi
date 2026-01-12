from typing import List, Dict, Any
from uuid import UUID
from sqlmodel import Session, select
from app.database import engine
from app.models import Alert, NewsArticle, SentimentAnalysis
import logging

logger = logging.getLogger(__name__)

class AlertEngine:
    """
    Evaluates alerts against new data events (e.g. new news, sentiment update).
    Condition format (JSON):
    {
        "type": "SENTIMENT",
        "value": "Adverse", 
        "company_id": "...", 
        "keyword": "optional"
    }
    """

    def check_alerts_for_article(self, article: NewsArticle, sentiment: SentimentAnalysis):
        """
        Check if any active alerts match this new article/sentiment.
        """
        with Session(engine) as session:
            # Find alerts for this company or global alerts
            # For MVP, we iterate active alerts for the user that are relevant
            # Optimization: Filter by company_id in condition if possible
            
            statement = select(Alert).where(Alert.is_active == True)
            alerts = session.exec(statement).all()
            
            triggered_alerts = []
            
            for alert in alerts:
                if self._evaluate_condition(alert.condition, article, sentiment):
                    self._trigger_alert(alert, article, sentiment)
                    triggered_alerts.append(alert)
                    
            return triggered_alerts

    def _evaluate_condition(self, condition: Dict, article: NewsArticle, sentiment: SentimentAnalysis) -> bool:
        try:
            # Check Company Match
            target_company_id = condition.get("company_id")
            if target_company_id and str(article.company_id) != str(target_company_id):
                return False

            # Check Sentiment Match
            target_sentiment = condition.get("sentiment")
            if target_sentiment and sentiment.score != target_sentiment:
                return False
                
            # Check Keyword Match (in Title or Content)
            keyword = condition.get("keyword")
            if keyword:
                keyword_lower = keyword.lower()
                if keyword_lower not in article.title.lower() and keyword_lower not in article.content.lower():
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating alert condition: {e}")
            return False

    def _trigger_alert(self, alert: Alert, article: NewsArticle, sentiment: SentimentAnalysis):
        """
        Dispatch notification (Log for MVP)
        """
        logger.info(f"ALERT TRIGGERED! AlertID: {alert.id} | User: {alert.user_id} | Reason: {sentiment.score} news on {article.title}")
        
        # In real world: Send Email / Push Notification / Save to Notification Table
        # Update last_triggered
        with Session(engine) as session:
            db_alert = session.get(Alert, alert.id)
            if db_alert:
                from datetime import datetime, timezone
                db_alert.last_triggered_at = datetime.now(timezone.utc)
                session.add(db_alert)
                session.commit()
