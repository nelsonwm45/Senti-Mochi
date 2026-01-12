## Relevant Files

- `backend/app/integrations/bursa_connector.py` (New) - Logic for fetching Bursa announcements.
- `backend/app/integrations/news_scraper.py` (New) - Generic scraper class for news sites.
- `backend/app/services/document_processor.py` - specific logic for PDF/OCR ingestion.
- `backend/app/tasks/ingestion_tasks.py` - Celery tasks for async ingestion.

### Notes

- Use `BeautifulSoup` or `Playwright` for scraping (if needed).
- OCR can use `pytesseract` or an external API (AWS Textract) depending on constraints. MVP might start with `pytesseract` or `pypdf`.

## Tasks

- [x] 0.0 Create feature branch
  - [x] 0.1 Create branch `feature/phase2-ingestion`
- [x] 1.0 Bursa Malaysia Connector
  - [x] 1.1 Create `BursaConnector` service to fetch announcements.
  - [x] 1.2 Implement logic to categorize announcements (Annual Reports vs Review vs General).
  - [x] 1.3 Create Celery task to poll Bursa periodically (e.g., every 15 mins).
- [x] 2.0 News Media Connectors
  - [x] 2.1 Build generic `NewsScraper` base class.
  - [x] 2.2 Implement specific scrapers for The Edge, The Star, NST.
  - [x] 2.3 Implement de-duplication logic (check if title/content hash exists in DB).
- [x] 3.0 Document Processor Pipeline
  - [x] 3.1 specific parser for PDF text extraction (enhance `ingest_service.py`).
  - [x] 3.2 Implement OCR fallback for image-based PDFs (using Tesseract or similar).
  - [x] 3.3 Create "Confidence Score" logic for extraction quality.
