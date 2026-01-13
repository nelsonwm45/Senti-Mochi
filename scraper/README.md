# Bursa PDF Scraper Service

A Flask-based service that downloads Bursa Malaysia announcement PDFs and stores them in a shared volume for easy access.

## Overview

This scraper service:
- Fetches Bursa disclosure pages using Playwright
- Extracts PDF links from disclosure HTML
- Downloads PDFs while maintaining proper browser context and cookies
- Stores files in a Docker volume for persistent access
- Provides REST API endpoints for the backend and frontend

## Architecture

### Components

1. **Flask API Server** (Port 5000)
   - `/fetch-disclosure` - Extract PDF links from a disclosure page
   - `/download-pdf` - Download and store a PDF
   - `/list-downloads` - List all downloaded files
   - `/health` - Health check endpoint

2. **Playwright Browser Engine**
   - Headless Chromium browser
   - Anti-detection features to avoid blocks
   - Async operations for efficient resource usage

3. **Persistent Volume**
   - `bursa_downloads` Docker volume
   - Shared with backend container at `/app/downloads`
   - Files are organized by company and timestamp

## File Structure

```
scraper/
├── app.py              # Flask application with Playwright logic
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container configuration
└── .dockerignore       # Docker build exclusions
```

## Docker Configuration

In `docker-compose.yml`:

```yaml
scraper:
  build:
    context: ./scraper
    dockerfile: Dockerfile
  container_name: bursa_scraper
  ports:
    - "5000:5000"
  volumes:
    - bursa_downloads:/app/downloads
  environment:
    - TZ=Asia/Kuala_Lumpur
  restart: unless-stopped
```

The `bursa_downloads` volume is also mounted to the backend at `/app/downloads`.

## API Endpoints

### 1. Fetch Disclosure PDFs
**GET** `/fetch-disclosure?id=<disclosure_id>`

Fetches the disclosure page and extracts all available PDF download links.

**Response:**
```json
{
  "pdfs": [
    {
      "name": "announcement.pdf",
      "url": "https://disclosure.bursamalaysia.com/..."
    }
  ]
}
```

### 2. Download PDF
**POST** `/download-pdf?disclosureId=<id>&filename=<name>&company_name=<company>`

Downloads a PDF and stores it in the volume.

**Request Body:**
```json
{
  "url": "https://disclosure.bursamalaysia.com/..."
}
```

**Response:**
```json
{
  "success": true,
  "filename": "announcement.pdf",
  "size": 1024000,
  "saved_path": "/app/downloads/20260113_180000_Maybank/announcement.pdf"
}
```

### 3. List Downloads
**GET** `/list-downloads`

Lists all downloaded files organized by folder.

**Response:**
```json
{
  "downloads": [
    {
      "folder": "20260113_180000_Maybank",
      "files": [
        {
          "name": "announcement.pdf",
          "size": 1024000,
          "path": "/downloads/20260113_180000_Maybank/announcement.pdf"
        }
      ],
      "count": 1
    }
  ],
  "total_folders": 1
}
```

## Backend Integration

The backend (`backend/app/routers/bursa.py`) proxies requests to the scraper service:

```python
from app.routers import bursa  # Bursa PDF download routes
```

Protected endpoints that call the scraper:
- `POST /api/v1/bursa/download-pdf` - Download a Bursa PDF
- `GET /api/v1/bursa/fetch-disclosure` - Fetch disclosure PDFs
- `GET /api/v1/bursa/list-downloads` - List downloaded files

## Frontend Usage

The dashboard (`frontend/src/app/dashboard/page.tsx`) includes a download button for Bursa announcements:

```tsx
<button onClick={() => handleDownloadBursaPDF(item, item.link, filename)}>
  <Download size={14} />
  Download PDF
</button>
```

When clicked:
1. Fetches available PDFs from the disclosure
2. Calls the backend `/api/v1/bursa/download-pdf` endpoint
3. Scraper downloads the PDF using Playwright
4. File is stored in the persistent volume
5. User receives confirmation message

## File Organization

Downloads are organized in the volume by company and timestamp:

```
bursa_downloads/
├── 20260113_180000_Maybank/
│   ├── announcement1.pdf
│   └── announcement2.pdf
├── 20260113_180015_Top_Glove/
│   └── disclosure_report.pdf
```

## Environment Variables

- `SCRAPER_URL` - URL of the scraper service (set in docker-compose: `http://scraper:5000`)
- `TZ` - Timezone (default: `Asia/Kuala_Lumpur`)

## Dependencies

See `requirements.txt`:
- `flask==3.0.0` - Web framework
- `playwright==1.40.0` - Browser automation
- `requests==2.31.0` - HTTP client
- `requests-html==0.10.0` - HTML parsing

## Building and Running

### With Docker Compose
```bash
cd /home/quahxuanyu/42KL/Ambank_Hackathon/Mochi
docker-compose up scraper
```

### Manual Build
```bash
docker build -t bursa-scraper ./scraper
docker run -p 5000:5000 -v bursa_downloads:/app/downloads bursa-scraper
```

## Troubleshooting

### PDF Download Fails
- Check if Playwright browsers are installed: `playwright install chromium`
- Verify disclosure ID is correct
- Check console logs for Bursa website changes

### Volume Permissions
- Ensure Docker has write access to the volume
- Check volume mount path consistency across services

### Scraper Timeout
- Increase timeout values in `app.py` (default: 60000ms)
- Check network connectivity to Bursa website

## Security Notes

- The scraper runs in a separate container for isolation
- Requests use User-Agent headers to avoid detection
- No credentials or sensitive data are stored
- Files are only accessible through authenticated backend endpoints

## Future Improvements

- [ ] Batch PDF downloads with progress tracking
- [ ] Automatic cleanup of old downloads
- [ ] PDF text extraction for search indexing
- [ ] Download retry logic with exponential backoff
- [ ] S3 integration for large-scale storage
