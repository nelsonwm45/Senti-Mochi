
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from uuid import UUID
from typing import List, Any

from app.database import get_session
from app.models import User, Company, Watchlist, UserRole
from app.auth import get_current_user
from app.services.finance import finance_service

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.post("", response_model=dict)
def add_to_watchlist(
    ticker: str = Query(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Add a company to the user's watchlist.
    """
    ticker = ticker.upper()
    
    # Check if company exists in DB
    statement = select(Company).where(Company.ticker == ticker)
    company = session.exec(statement).first()
    
    if not company:
        # Fetch from yfinance
        info = finance_service.get_company_info(ticker)
        if not info:
             raise HTTPException(status_code=404, detail="Company not found in external source")
        
        company = Company(**info)
        session.add(company)
        session.commit()
        session.refresh(company)
    
    # Check if already in watchlist
    statement = select(Watchlist).where(Watchlist.user_id == current_user.id, Watchlist.company_id == company.id)
    existing = session.exec(statement).first()
    if existing:
        return {"message": "Company already in watchlist"}
    
    watchlist_item = Watchlist(user_id=current_user.id, company_id=company.id)
    session.add(watchlist_item)
    session.commit()
    
    # Trigger immediate news fetch for this company (Hybrid Option C)
    try:
        from app.tasks.data_tasks import update_company_news_task
        update_company_news_task.delay(ticker)
        print(f"[WATCHLIST] Triggered news fetch for {ticker}")
    except Exception as e:
        print(f"[WATCHLIST] Failed to trigger news fetch: {e}")
        # Don't fail the watchlist add if news fetch fails
    
    return {"message": "Added to watchlist", "company": company.name}

@router.get("/my-watchlist", response_model=List[dict])
def get_my_watchlist(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's watchlist with company details.
    """
    statement = select(Company).join(Watchlist).where(Watchlist.user_id == current_user.id)
    companies = session.exec(statement).all()
    
    return [
        {
            "id": str(company.id),
            "name": company.name,
            "ticker": company.ticker,
            "common_name": company.common_name,  # Include for news search
            "sector": company.sector,
            "sub_sector": company.sub_sector,
            "website_url": company.website_url
        }
        for company in companies
    ]

@router.get("", response_model=List[dict])
def get_watchlist(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's watchlist with company details (returns full company objects).
    """
    statement = select(Company).join(Watchlist).where(Watchlist.user_id == current_user.id)
    companies = session.exec(statement).all()
    
    return [
        {
            "id": str(company.id),
            "name": company.name,
            "ticker": company.ticker,
            "common_name": company.common_name,  # Include for news search
            "sector": company.sector,
            "sub_sector": company.sub_sector,
            "website_url": company.website_url
        }
        for company in companies
    ]

@router.delete("/{ticker}", response_model=dict)
def remove_from_watchlist(
    ticker: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a company from the watchlist.
    """
    ticker = ticker.upper()
    statement = select(Watchlist).join(Company).where(
        Watchlist.user_id == current_user.id,
        Company.ticker == ticker
    )
    watchlist_item = session.exec(statement).first()
    
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="Company not found in watchlist")
    
    session.delete(watchlist_item)
    session.commit()
    return {"message": "Removed from watchlist"}

def _resolve_user_id(identifier: str, session: Session) -> UUID:
    try:
        return UUID(identifier)
    except ValueError:
        pass
        
    # Valid email?
    if "@" in identifier:
        statement = select(User).where(User.email == identifier)
        user = session.exec(statement).first()
        if user:
            return user.id
            
    # If we are here, we couldn't resolve. 
    # For MVP dev convenience, if the user doesn't exist but looks like an email, 
    # we might want to fail hard, or... 
    # But since signup is separate, we should just fail.
    raise HTTPException(status_code=404, detail=f"User not found: {identifier}")
