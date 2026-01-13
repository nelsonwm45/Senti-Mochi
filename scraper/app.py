from flask import Flask, request, jsonify
import re
import asyncio
import os
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

app = Flask(__name__)

# Ensure downloads directory exists
DOWNLOADS_DIR = Path('/app/downloads')
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


async def fetch_disclosure_async(disclosure_id):
    """Fetch disclosure page using Playwright"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            url = f'https://disclosure.bursamalaysia.com/FileAccess/viewHtml?e={disclosure_id}'
            print(f'Fetching: {url}')
            
            await page.goto(url, wait_until='load', timeout=60000)
            
            # Wait for the content to be rendered
            await page.wait_for_timeout(3000)
            
            html = await page.content()
            
            print(f'HTML length: {len(html)}')
            
            await context.close()
            await browser.close()
            
            return html
        except Exception as e:
            print(f'Error during fetch: {str(e)}')
            await context.close()
            await browser.close()
            raise e


async def download_pdf_async(pdf_url, disclosure_id):
    """Download PDF using Playwright by fetching from within the page context"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            print(f'Downloading PDF from: {pdf_url}')
            
            # Navigate to the disclosure page first to set up the context
            disclosure_url = f'https://disclosure.bursamalaysia.com/FileAccess/viewHtml?e={disclosure_id}'
            await page.goto(disclosure_url, wait_until='load', timeout=60000)
            
            print('Navigated to disclosure page')
            
            # Wait a moment for any cookies to be set
            await page.wait_for_timeout(1000)
            
            # Use the browser's fetch API to get the PDF - this automatically includes cookies
            # and maintains the proper context
            pdf_data = await page.evaluate(f'''
                async () => {{
                    const response = await fetch('{pdf_url}', {{
                        headers: {{
                            'Accept': 'application/pdf'
                        }}
                    }});
                    if (!response.ok) {{
                        throw new Error(`HTTP error! status: ${{response.status}}`);
                    }}
                    const buffer = await response.arrayBuffer();
                    return Array.from(new Uint8Array(buffer));
                }}
            ''')
            
            # Convert array back to bytes
            pdf_buffer = bytes(pdf_data)
            
            print(f'Got PDF content: {len(pdf_buffer)} bytes')
            
            await context.close()
            await browser.close()
            
            return pdf_buffer
        except Exception as e:
            print(f'Error during PDF download: {str(e)}')
            import traceback
            traceback.print_exc()
            await context.close()
            await browser.close()
            raise e


@app.route('/fetch-disclosure', methods=['GET'])
def fetch_disclosure():
    disclosure_id = request.args.get('id')
    
    if not disclosure_id:
        return jsonify({'error': 'Missing disclosure ID'}), 400
    
    try:
        # Run async function in event loop
        html = asyncio.run(fetch_disclosure_async(disclosure_id))
        
        if not html or len(html) < 500:
            print(f'HTML too short: {len(html) if html else 0}')
            return jsonify({'error': 'Failed to load page content'}), 429
        
        print(f'Full HTML length: {len(html)}')
        
        # Extract PDF links - the HTML uses double quotes and &amp; entities
        links = []
        
        # Pattern 1: Match the att_download_pdf paragraphs with proper quote handling
        pdf_regex = r'<p\s+class="att_download_pdf">\s*<a\s+href="([^"]+)"[^>]*>\s*([^<]+\.pdf)\s*<\/a>'
        matches = re.finditer(pdf_regex, html, re.IGNORECASE)
        
        for match in matches:
            url = match.group(1)
            name = match.group(2).strip()
            # Decode HTML entities
            url = url.replace('&amp;', '&')
            links.append({
                'name': name,
                'url': f'https://disclosure.bursamalaysia.com{url}'
            })
        
        print(f'Found {len(links)} PDF links with pattern 1')
        
        # Pattern 2: If pattern 1 didn't work, try with single quotes
        if not links:
            pdf_regex = r"<p\s+class='att_download_pdf'>\s*<a\s+href='([^']+)'[^>]*>\s*([^<]+\.pdf)\s*<\/a>"
            matches = re.finditer(pdf_regex, html, re.IGNORECASE)
            for match in matches:
                url = match.group(1)
                name = match.group(2).strip()
                url = url.replace('&amp;', '&')
                links.append({
                    'name': name,
                    'url': f'https://disclosure.bursamalaysia.com{url}'
                })
            print(f'Found {len(links)} PDF links with pattern 2')
        
        if links:
            print(f'Successfully extracted {len(links)} PDFs')
            for link in links:
                print(f'  - {link["name"]}: {link["url"][:80]}...')
        else:
            # Debug: check what we're looking for
            if 'att_download_pdf' in html:
                print('Found att_download_pdf in HTML but regex didnt match')
            else:
                print('att_download_pdf not found in HTML')
        
        return jsonify({'pdfs': links}), 200
    
    except Exception as e:
        print(f'Error in fetch_disclosure: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    data = request.get_json()
    pdf_url = data.get('url')
    disclosure_id = request.args.get('disclosureId')
    filename = request.args.get('filename', 'document.pdf')
    company_name = request.args.get('company_name', 'unknown')
    
    if not pdf_url:
        return jsonify({'error': 'Missing PDF URL'}), 400
    
    try:
        # Run async function in event loop
        buffer = asyncio.run(download_pdf_async(pdf_url, disclosure_id))
        
        print(f'Downloaded PDF: {filename} ({len(buffer)} bytes)')
        
        # Create a subdirectory with timestamp and company name for organization
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_dir = DOWNLOADS_DIR / f'{timestamp}_{company_name}'
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        file_path = save_dir / filename
        with open(file_path, 'wb') as f:
            f.write(buffer)
        
        print(f'Saved PDF to: {file_path}')
        
        return jsonify({
            'success': True,
            'filename': filename,
            'size': len(buffer),
            'saved_path': str(file_path)
        }), 200
    
    except Exception as e:
        print(f'Error in download_pdf: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/list-downloads', methods=['GET'])
def list_downloads():
    """List all downloaded files organized by folder"""
    try:
        downloads = []
        if DOWNLOADS_DIR.exists():
            for folder in sorted(DOWNLOADS_DIR.iterdir(), reverse=True):
                if folder.is_dir():
                    files = []
                    for file in sorted(folder.iterdir()):
                        if file.is_file():
                            files.append({
                                'name': file.name,
                                'size': file.stat().st_size,
                                'path': f'/downloads/{folder.name}/{file.name}'
                            })
                    if files:
                        downloads.append({
                            'folder': folder.name,
                            'files': files,
                            'count': len(files)
                        })
        
        return jsonify({'downloads': downloads, 'total_folders': len(downloads)}), 200
    except Exception as e:
        print(f'Error listing downloads: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
