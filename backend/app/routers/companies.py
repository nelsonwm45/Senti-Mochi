
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Dict, Any

from app.database import get_session
from app.models import Company
from app.services.finance import finance_service

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/compare")
def compare_companies(
    tickers: List[str] = Query(..., description="List of tickers to compare"),
    session: Session = Depends(get_session)
):
    """
    Compare multiple companies side-by-side.
    """
    results = []
    for ticker in tickers:
        ticker = ticker.upper()
        # Ensure company exists in DB or fetch basic info? 
        # Actually, for comparison we mainly want the live data.
        # But let's check DB for static info (Sector, Name) and yfinance for dynamic (Financials)
        
        statement = select(Company).where(Company.ticker == ticker)
        company = session.exec(statement).first()
        
        info = {}
        if company:
            info = {
                "name": company.name,
                "ticker": company.ticker,
                "sector": company.sector,
                "sub_sector": company.sub_sector
            }
        else:
             # Try fetch basic info if not in DB
             basic = finance_service.get_company_info(ticker)
             if basic:
                 info = basic
             else:
                 info = {"ticker": ticker, "error": "Not found"}

        if "error" not in info:
             financials = finance_service.get_financials(ticker)
             info.update(financials)
        
        results.append(info)
        
    return results

@router.get("/search")
def search_companies(
    query: str | None = None,
    limit: int = 20,
    session: Session = Depends(get_session)
):
    """
    Search for companies by ticker or name.
    If query is empty, returns first {limit} companies.
    """
    statement = select(Company)
    
    if query:
        query = query.strip().lower()
        statement = statement.where(
            (Company.ticker.ilike(f"%{query}%")) | 
            (Company.name.ilike(f"%{query}%"))
        )
    
    statement = statement.limit(limit)
    
    companies = session.exec(statement).all()
    
    return [
        {
            "id": str(c.id),
            "ticker": c.ticker,
            "name": c.name,
            "sector": c.sector,
            "sub_sector": c.sub_sector
        }
        for c in companies
    ]

@router.get("/{ticker}")
def get_company_details(
    ticker: str,
    session: Session = Depends(get_session)
):
    """
    Get detailed info for a specific company.
    """
    ticker = ticker.upper()
    
    statement = select(Company).where(Company.ticker == ticker)
    company = session.exec(statement).first()
    
    info = {}
    if company:
        info = {
            "name": company.name,
            "id": str(company.id),
            "ticker": company.ticker,
            "sector": company.sector,
            "sub_sector": company.sub_sector,
            "website_url": company.website_url,
            "description": "" # Add if available
        }
    else:
         basic = finance_service.get_company_info(ticker)
         if basic:
             info = basic
         else:
             raise HTTPException(status_code=404, detail="Company not found")

    # Always fetch latest financials
    financials = finance_service.get_financials(ticker)
    info.update(financials)
    
    return info
