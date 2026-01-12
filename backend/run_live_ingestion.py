import logging
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from datetime import datetime
from sqlmodel import Session
from app.database import engine
from app.models import NewsArticle, SentimentAnalysis
from app.services.sentiment_engine import SentimentEngine
from app.integrations.news_scraper import TheEdgeScraper, TheStarScraper, FMTScraper
from app.ai_service import summarize_article

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def resolve_url(url: str) -> str:
    """Resolves potential redirects (especially Google News)."""
    try:
        if "news.google.com" not in url:
            return url
            
        headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' }
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        return response.url
    except:
        return url

def fetch_article_content(url: str) -> str:
    """Uses newspaper3k to extract main article text."""
    try:
        final_url = resolve_url(url)
        logger.info(f"Resolved {url[:30]}... to {final_url[:50]}...")
        
        article = Article(final_url)
        article.download()
        article.parse()
        
        text = article.text
        if len(text) < 200:
             # Try falling back to meta description?
             meta = article.meta_description
             if meta and len(meta) > 50 and "Google News" not in meta:
                 return f"META:{meta}"
             return ""
             
        return text
    except Exception as e:
        logger.warning(f"Newspaper extraction failed for {url}: {e}")
        return ""

def is_redundant(summary: str, title: str) -> bool:
    """Checks if summary is too similar to title using token overlap."""
    if not summary or not title:
        return False
        
    def tokenize(text):
        return set(text.lower().replace('-', ' ').split())
        
    s_tokens = tokenize(summary)
    t_tokens = tokenize(title)
    
    # Calculate overlap ratio
    common = s_tokens.intersection(t_tokens)
    overlap_ratio = len(common) / len(s_tokens) if s_tokens else 0
    
    title_coverage = len(common) / len(t_tokens) if t_tokens else 0
    
    if overlap_ratio > 0.6 or title_coverage > 0.8:
        return True
            
    return False

def run_ingestion():
    logger.info("Starting Live Ingestion...")
    sentiment_engine = SentimentEngine()
    
    scrapers = [TheEdgeScraper(), TheStarScraper(), FMTScraper()]
    
    with Session(engine) as session:
        for scraper in scrapers:
            logger.info(f"Running scraper: {scraper.source_name}")
            try:
                articles_data = scraper.scrape()
                logger.info(f"Found {len(articles_data)} articles from {scraper.source_name}")
                
                for art_data in articles_data:
                    # Check if exists
                    existing = session.get(NewsArticle, art_data['id'])
                    if existing:
                        continue
                    
                    # 1. Determine Content
                    full_text = ""
                    # If scraper provided substantial content (like FMT/TheStar might), use it
                    provided_content = art_data.get('content', '')
                    if len(provided_content) > 300:
                        full_text = provided_content
                    else:
                        # Otherwise fetch external
                        logger.info(f"Fetching full text for: {art_data['title']}")
                        full_text = fetch_article_content(art_data['url'])
                    
                    # 1b. Summarize
                    summary = None
                    if full_text and full_text.startswith("META:"):
                        summary = full_text[5:] # Strip prefix
                    elif full_text and len(full_text) > 300:
                        logger.info("Generating summary from full text...")
                        summary = summarize_article(full_text)
                    
                    # Fallback to RSS description/provided content if summary is still None
                    if not summary:
                        desc = art_data.get('description', '')
                        if len(desc) > 50:
                            summary = desc
                    
                    # Final Redundancy Check
                    if summary and is_redundant(summary, art_data['title']):
                        logger.info(f"Summary redundant for {art_data['title'][:20]}...")
                        summary = None

                    # if not summary:
                    #     summary = "Click title to read full article content."

                    # Create Article
                    article = NewsArticle(
                        id=art_data['id'],
                        title=art_data['title'],
                        url=art_data['url'],
                        source_name=art_data['source'],
                        published_at=art_data['published_at'] or datetime.now(),
                        content=full_text if full_text else art_data.get('content', art_data['title']),
                        article_content=full_text,
                        summary=summary
                    )
                    
                    session.add(article)
                    session.commit()
                    print(f"Saved Article: {article.title}")
                    
                    # 2. Analyze Sentiment
                    try:
                        sentiment = sentiment_engine.process_news(article.id)
                    except Exception as e:
                        logger.error(f"Sentiment failed: {e}")
                        
            except Exception as e:
                logger.error(f"Scraper {scraper.source_name} failed: {e}")

    logger.info("Live Ingestion Complete.")

if __name__ == "__main__":
    run_ingestion()
