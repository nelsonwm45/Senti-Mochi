from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Optional
import httpx
import os
from app.auth import get_current_user
from app.models import User
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/bursa", tags=["bursa"])

# Get scraper URL from environment
SCRAPER_URL = os.getenv("SCRAPER_URL", "http://scraper:5000")


class FetchPDFRequest(BaseModel):
    disclosure_id: str
    pdf_url: str
    filename: str
    company_name: str


class FetchPDFResponse(BaseModel):
    success: bool
    filename: str
    size: Optional[int] = None
    message: str


@router.post("/download-pdf", response_model=FetchPDFResponse)
async def download_bursa_pdf(
    request: FetchPDFRequest,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """
    Download a Bursa PDF announcement and store it in the downloads volume
    
    - Receives PDF details from frontend
    - Calls scraper service to fetch and store the PDF
    - Returns confirmation with file details
    """
    try:
        # Call the scraper service to download the PDF
        async with httpx.AsyncClient(timeout=120.0) as client:
            scraper_response = await client.post(
                f"{SCRAPER_URL}/download-pdf",
                json={"url": request.pdf_url},
                params={
                    "disclosureId": request.disclosure_id,
                    "filename": request.filename,
                    "company_name": request.company_name
                }
            )
            
            if scraper_response.status_code != 200:
                error_data = scraper_response.json()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Scraper error: {error_data.get('error', 'Unknown error')}"
                )
            
            result = scraper_response.json()
            return FetchPDFResponse(
                success=result.get("success", True),
                filename=result.get("filename"),
                size=result.get("size"),
                message=f"PDF downloaded successfully: {request.filename}"
            )
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect to scraper service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading PDF: {str(e)}"
        )


@router.get("/fetch-disclosure")
async def fetch_disclosure_pdfs(
    disclosure_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Fetch available PDFs for a disclosure ID from Bursa
    
    - Calls scraper to get the disclosure page
    - Extracts all PDF download links
    - Returns list of available PDFs
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            scraper_response = await client.get(
                f"{SCRAPER_URL}/fetch-disclosure",
                params={"id": disclosure_id}
            )
            
            if scraper_response.status_code != 200:
                error_data = scraper_response.json()
                raise HTTPException(
                    status_code=scraper_response.status_code,
                    detail=f"Scraper error: {error_data.get('error', 'Unknown error')}"
                )
            
            return scraper_response.json()
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect to scraper service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching disclosure: {str(e)}"
        )


@router.get("/list-downloads")
async def list_downloads(
    current_user: User = Depends(get_current_user)
):
    """
    List all downloaded Bursa PDF files
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            scraper_response = await client.get(
                f"{SCRAPER_URL}/list-downloads"
            )
            
            if scraper_response.status_code != 200:
                error_data = scraper_response.json()
                raise HTTPException(
                    status_code=scraper_response.status_code,
                    detail=f"Scraper error: {error_data.get('error', 'Unknown error')}"
                )
            
            return scraper_response.json()
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect to scraper service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing downloads: {str(e)}"
        )
