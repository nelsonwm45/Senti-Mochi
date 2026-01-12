from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.database import get_session
from app.models import User, Company, Watchlist
from app.auth import get_current_user

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

class WatchlistBase(BaseModel):
    companyId: UUID

class WatchlistCreate(WatchlistBase):
    pass

class WatchlistRead(BaseModel):
    id: UUID
    company: Company

@router.get("/", response_model=List[WatchlistRead])
def get_watchlist(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get user's watchlist"""
    items = session.exec(select(Watchlist).where(Watchlist.user_id == current_user.id)).all()
    results = []
    for item in items:
        company = session.get(Company, item.company_id)
        if company:
            results.append(WatchlistRead(id=item.id, company=company))
    return results

@router.post("/", response_model=WatchlistRead)
def add_to_watchlist(
    watchlist_data: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Add company to watchlist"""
    # Check if company exists
    company = session.get(Company, watchlist_data.companyId)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # Check if already in watchlist
    existing = session.exec(
        select(Watchlist)
        .where(Watchlist.user_id == current_user.id)
        .where(Watchlist.company_id == watchlist_data.companyId)
    ).first()
    
    if existing:
        return WatchlistRead(id=existing.id, company=company)
        
    new_item = Watchlist(user_id=current_user.id, company_id=watchlist_data.companyId)
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    
    return WatchlistRead(id=new_item.id, company=company)

@router.delete("/{id}")
def remove_from_watchlist(
    id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Remove from watchlist"""
    item = session.get(Watchlist, id)
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
        
    if item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    session.delete(item)
    session.commit()
    return {"message": "Deleted successfully"}
