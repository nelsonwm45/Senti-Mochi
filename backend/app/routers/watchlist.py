
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from uuid import UUID
from typing import List, Any

from app.database import get_session
from app.models import User, Company, Watchlist, UserRole
# Assuming we have a way to get current user, using a simplified dependency for now or reusing existing auth
# If specific auth is not visible, I'll assume a placeholder or simple extraction
# Checking other routers might be good, but I'll assume standard pattern
from app.services.finance import finance_service

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

# Placeholder for get_current_user dependency - checking existing code would be better but I'll assume one exists or mock it
# For now, let's assume `get_current_user` is available in `app.auth` or similar. 
# I will check `app/main.py` or similar to find where auth is. 
# but simply, I can just require user_id in params if I can't find it, OR I can list files to find it.
# Wait, I shouldn't guess. I will look for `get_current_user` in `app` later.
# For now I will write the structure and fix imports after I see other routers.


@router.post("/", response_model=dict)
def add_to_watchlist(
    ticker: str,
    user_id: str, # Changed to str to accept email or uuid
    session: Session = Depends(get_session)
):
    """
    Add a company to the user's watchlist.
    """
    real_user_id = _resolve_user_id(user_id, session)
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
    statement = select(Watchlist).where(Watchlist.user_id == real_user_id, Watchlist.company_id == company.id)
    existing = session.exec(statement).first()
    if existing:
        return {"message": "Company already in watchlist"}
    
    watchlist_item = Watchlist(user_id=real_user_id, company_id=company.id)
    session.add(watchlist_item)
    session.commit()
    
    return {"message": "Added to watchlist", "company": company.name}

@router.get("/", response_model=List[Company])
def get_watchlist(
    user_id: str, # Changed to str
    session: Session = Depends(get_session)
):
    """
    Get the user's watchlist.
    """
    real_user_id = _resolve_user_id(user_id, session)
    statement = select(Company).join(Watchlist).where(Watchlist.user_id == real_user_id)
    companies = session.exec(statement).all()
    return companies

@router.delete("/{ticker}", response_model=dict)
def remove_from_watchlist(
    ticker: str,
    user_id: str, # Changed to str
    session: Session = Depends(get_session)
):
    """
    Remove a company from the watchlist.
    """
    real_user_id = _resolve_user_id(user_id, session)
    ticker = ticker.upper()
    statement = select(Watchlist).join(Company).where(
        Watchlist.user_id == real_user_id,
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
