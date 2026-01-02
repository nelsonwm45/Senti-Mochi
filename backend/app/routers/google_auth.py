from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
import os
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from app.auth import create_access_token, get_password_hash
import secrets

router = APIRouter(prefix="/auth/google", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# Assuming frontend is on localhost:3000 and backend on localhost:8000
REDIRECT_URI = "http://localhost:8000/auth/google/callback"
FRONTEND_URL = "http://localhost:3000"

@router.get("/login")
async def google_login():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Client ID not configured")
        
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid%20email%20profile"
    )

@router.get("/callback")
async def google_callback(code: str, session: Session = Depends(get_session)):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
         raise HTTPException(status_code=500, detail="Google credentials not configured")

    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        res = await client.post(token_url, data=data)
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to retrieve token from Google")
        
        token_data = res.json()
        access_token = token_data.get("access_token")

        # Get user info
        user_info_res = await client.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {access_token}"})
        if user_info_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")
            
        user_info = user_info_res.json()
        email = user_info.get("email")
        name = user_info.get("name")
        
        if not email:
            raise HTTPException(status_code=400, detail="Google email not found")

        # Check if user exists
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()

        if not user:
            # Create new user
            # Generate a random password since they use Google to login
            random_password = secrets.token_urlsafe(16)
            hashed_password = get_password_hash(random_password)
            user = User(email=email, full_name=name, hashed_password=hashed_password)
            session.add(user)
            session.commit()
            session.refresh(user)

        # Create JWT token
        access_token_jwt = create_access_token(data={"sub": user.email})
        
        # Redirect to frontend with token
        return RedirectResponse(f"{FRONTEND_URL}/google-callback?token={access_token_jwt}")
