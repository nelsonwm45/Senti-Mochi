from app.integrations.bursa_connector import BursaConnector
from app.integrations.news_scraper import TheEdgeScraper
from app.services.document_processor import DocumentProcessor

def verify_phase2():
    print("--- Verifying Bursa Connector ---")
    bursa = BursaConnector()
    announcements = bursa.fetch_announcements()
    print(f"Fetched {len(announcements)} announcements.")
    print(f"First item: {announcements[0]['title']}")

    print("\n--- Verifying News Scraper ---")
    scraper = TheEdgeScraper()
    articles = scraper.scrape()
    print(f"Fetched {len(articles)} articles from The Edge.")
    print(f"First item: {articles[0]['title']}")

    print("\n--- Verifying Document Processor Import ---")
    dp = DocumentProcessor()
    print("DocumentProcessor initialized successfully.")

if __name__ == "__main__":
    verify_phase2()
