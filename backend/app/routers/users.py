from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import User, ClientProfile
from app.auth import get_current_user
from app.ai_service import get_financial_advice
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])

class ProfileUpdate(BaseModel):
    financial_goals: str
    risk_tolerance: str
    assets_value: float

class AdviceResponse(BaseModel):
    advice: str

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/profile", response_model=ClientProfile | None)
def get_profile(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    profile = session.exec(select(ClientProfile).where(ClientProfile.user_id == current_user.id)).first()
    return profile

@router.post("/profile", response_model=ClientProfile)
def update_profile(profile_data: ProfileUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    profile = session.exec(select(ClientProfile).where(ClientProfile.user_id == current_user.id)).first()
    if not profile:
        profile = ClientProfile(user_id=current_user.id, **profile_data.dict())
        session.add(profile)
    else:
        profile.financial_goals = profile_data.financial_goals
        profile.risk_tolerance = profile_data.risk_tolerance
        profile.assets_value = profile_data.assets_value
        session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile

@router.post("/advice", response_model=AdviceResponse)
def get_ai_advice(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    profile = session.exec(select(ClientProfile).where(ClientProfile.user_id == current_user.id)).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not found. Please complete your profile logic.")
    
    summary = f"Goals: {profile.financial_goals}, Risk: {profile.risk_tolerance}, Assets: ${profile.assets_value}"
    advice = get_financial_advice(summary)
    return {"advice": advice}
