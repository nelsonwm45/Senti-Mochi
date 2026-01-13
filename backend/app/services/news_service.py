import requests
from datetime import datetime
from sqlmodel import Session, select
from app.database import engine
from app.models import Company, NewsArticle
import urllib.parse
from app.services.company_service import company_service

class NewsService:
    @staticmethod
    def fetch_bursa_news(company: Company):
        """
        Fetch announcements from Bursa Malaysia for a specific company.
        """
        if not company.ticker:
            return []
            
        bursa_code = company.ticker.split('.')[0]
        url = f"https://www.bursamalaysia.com/api/v1/announcements/search?ann_type=company&company={bursa_code}&per_page=5&page=1"
        
        try:
            response = requests.get(url, headers={'Accept': 'application/json'}, timeout=10)
            if response.status_code != 200:
                print(f"Bursa API error for {company.name}: {response.status_code}")
                return []
            
            data = response.json()
            if not data.get('data'):
                return []

            articles = []
            for item in data['data']:
                # Item format: [id, date_html, company_html, title_html]
                # We need to parse this somewhat manually or use robust regex
                # Ideally we want a cleaner API but this is what we have.
                # For backend parsing, regex is safer than full HTML parser for simple snippets.
                import re
                
                # Extract date
                # <a href='/market_information/announcements/company_announcement/hunza-properties-berhad?ann_id=123'>15 Jan 2026...</a>
                date_match = re.search(r'>([^<]+)</a>', item[1])
                date_str = date_match.group(1).strip() if date_match else "Unknown Date"
                
                # Extract Title & Link
                # <a href='/market...'>Title</a>
                title_match = re.search(r"href='([^']+)'[^>]*>(.*?)</a>", item[3])
                link_suffix = title_match.group(1) if title_match else ""
                title = title_match.group(2).strip() if title_match else "Unknown Title"
                
                # Full link
                link = f"https://www.bursamalaysia.com{link_suffix}" if link_suffix else ""
                
                # ID extraction from link usually safer: ann_id=3412702
                id_match = re.search(r"ann_id=(\d+)", link)
                native_id = f"bursa-{bursa_code}-{id_match.group(1)}" if id_match else f"bursa-{bursa_code}-{item[0]}"
                
                # Parse date
                try:
                    # Format: "13 Jan 2026, 05:44 pm"
                    published_at = datetime.strptime(date_str, "%d %b %Y, %I:%M %p")
                except:
                    published_at = datetime.utcnow()

                articles.append(NewsArticle(
                    company_id=company.id,
                    source="bursa",
                    native_id=native_id,
                    title=title,
                    url=link,
                    published_at=published_at,
                    content=title # Saving title as content for now
                ))
            return articles

        except Exception as e:
            print(f"Error fetching Bursa for {company.name}: {e}")
            return []

    @staticmethod
    def fetch_star_news(company: Company):
        """
        Fetch news from The Star via Queryly API.
        """
        query = urllib.parse.quote(company.name)
        url = f"https://api.queryly.com/json.aspx?queryly_key=6ddd278bf17648ac&query={query}&endindex=0&batchsize=5&showfaceted=true&extendeddatafields=paywalltype,isexclusive,kicker,kickerurl,summary,sponsor&timezoneoffset=-450"
        
        try:
            response = requests.get(url, headers={'Accept': 'application/json'}, timeout=10)
            if response.status_code != 200:
                print(f"Star API error for {company.name}: {response.status_code}")
                return []
            
            # The API might return JSONP `resultcallback({...})` or pure JSON
            text = response.text
            if 'resultcallback' in text:
                import json
                match = re.search(r'resultcallback\s*\(\s*({[\s\S]*})\s*\)', text)
                if match:
                    data = json.loads(match.group(1))
                else:
                    return []
            else:
                data = response.json()
            
            items = data.get('items', [])
            articles = []
            
            for item in items:
                # published format: "2026-01-12 16:30:00" approx? 
                # Actually item['pubdate'] is usually "Jan 12, 2026"
                # But pubdateunix is reliable
                try:
                    published_at = datetime.fromtimestamp(item.get('pubdateunix', 0))
                except:
                    published_at = datetime.utcnow()
                    
                native_id = f"star-{company.ticker}-{item.get('_id')}"
                
                articles.append(NewsArticle(
                    company_id=company.id,
                    source="star",
                    native_id=native_id,
                    title=item.get('title'),
                    url=item.get('link'),
                    published_at=published_at,
                    content=item.get('description') or item.get('summary')
                ))
            return articles
            
        except Exception as e:
            print(f"Error fetching Star for {company.name}: {e}")
            return []

    @staticmethod
    def fetch_nst_news(company: Company):
        """
        Fetch news from NST API.
        """
        query = urllib.parse.quote(company.name)
        # Using the URL found in frontend route.ts
        # https://www.nst.com.my/api/search?keywords=...
        url = f"https://www.nst.com.my/api/search?keywords={query}&category=&sort=DESC&page_size=5&page=0"
        
        try:
            response = requests.get(url, headers={
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            }, timeout=10)
            
            if response.status_code != 200:
                print(f"NST API error for {company.name}: {response.status_code}")
                return []
                
            data = response.json()
            items = data.get('data', [])
            articles = []
            
            for item in items:
                # item['created'] is timestamp
                try:
                    published_at = datetime.fromtimestamp(item.get('created', 0))
                except:
                    published_at = datetime.utcnow()
                
                native_id = f"nst-{company.ticker}-{item.get('nid')}"
                
                articles.append(NewsArticle(
                    company_id=company.id,
                    source="nst",
                    native_id=native_id,
                    title=item.get('title'),
                    url=item.get('url'),
                    published_at=published_at,
                    content=item.get('field_article_lead')
                ))
            return articles
            
        except Exception as e:
            print(f"Error fetching NST for {company.name}: {e}")
            return []

    @staticmethod
    def get_company_news_context(company_id: str, session: Session, limit: int = 5) -> str:
        """
        Retrieve recent news for a company formatted for LLM context.
        """
        stmt = select(NewsArticle).where(NewsArticle.company_id == company_id).order_by(NewsArticle.published_at.desc()).limit(limit)
        articles = session.exec(stmt).all()
        
        if not articles:
            return ""
            
        summary = "Recent News Headlines:\n"
        for article in articles:
            date_str = article.published_at.strftime("%Y-%m-%d")
            summary += f"- [{date_str}] {article.title} (Source: {article.source})\n"
            # Optional: Add content snippet if available and useful
            
        return summary + "\n"
    
    @staticmethod
    def sync_news(company_id: int = None, session: Session = None):
        """
        Main method to sync news for companies.
        If company_id is provided, sync only that company.
        Otherwise, sync all companies.
        """
        local_session = False
        if not session:
            session = Session(engine)
            local_session = True
            
        try:
            # Get companies to sync
            if company_id:
                # Sync single company
                company = session.get(Company, company_id)
                if not company:
                    print(f"Company ID {company_id} not found")
                    return 0
                companies = [company]
            else:
                # Sync all companies
                companies = session.exec(select(Company)).all()
            
            print(f"Syncing news for {len(companies)} companies...")
            
            total_saved = 0
            for company in companies:
                new_articles = []
                # Fetch from all sources
                new_articles.extend(NewsService.fetch_bursa_news(company))
                new_articles.extend(NewsService.fetch_star_news(company))
                new_articles.extend(NewsService.fetch_nst_news(company))
                
                count = 0
                for article in new_articles:
                    # Upsert check - rudimentary
                    existing = session.exec(select(NewsArticle).where(
                        NewsArticle.native_id == article.native_id
                    )).first()
                    
                    if not existing:
                        session.add(article)
                        count += 1
                
                if count > 0:
                    session.commit()
                    print(f"Saved {count} new articles for {company.name}")
                    total_saved += count
            
            return total_saved
                
        finally:
            if local_session:
                session.close()

news_service = NewsService()
