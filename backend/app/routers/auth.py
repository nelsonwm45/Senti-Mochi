from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from app.auth import get_password_hash, verify_password, create_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/signup", response_model=Token)
def signup(user: UserCreate, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password, full_name=user.full_name)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # Check if companies need seeding (same as login)
    print(f"[SIGNUP] User {new_user.email} created successfully")
    try:
        from app.services.company_service import company_service
        from app.tasks.company_tasks import seed_companies_task
        from app.tasks.data_tasks import update_all_news_task
        
        count = company_service.get_company_count(session)
        print(f"[SIGNUP] Company count: {count}")
        
        if count == 0:
            print("[SIGNUP] No companies found. Triggering automated seeding task...")
            seed_companies_task.delay()
            print("[SIGNUP] Auto-seeding tasks queued successfully")
        else:
            print(f"[SIGNUP] Companies already exist ({count}), skipping auto-seeding")
    except Exception as e:
        print(f"[SIGNUP] Failed to trigger auto-seeding: {e}")
        import traceback
        traceback.print_exc()
    
    # Create and return access token
    access_token = create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    
    # Check if companies need seeding
    try:
        from app.services.company_service import company_service
        from app.tasks.company_tasks import seed_companies_task
        from app.tasks.data_tasks import update_all_news_task
        
        count = company_service.get_company_count(session)
        if count == 0:
            print("No companies found. Triggering automated seeding task...")
            seed_companies_task.delay()
    except Exception as e:
        print(f"Failed to trigger auto-seeding: {e}")

    return {"access_token": access_token, "token_type": "bearer"}
