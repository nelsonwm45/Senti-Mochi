from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from app.database import get_session
from app.models import User, ClientProfile, UserRole
from app.auth import get_current_user, require_role
from app.ai_service import get_financial_advice
from pydantic import BaseModel
import boto3
import os
from datetime import datetime, timezone
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/users", tags=["users"])

# Initialize S3 client (using Minio for local development)
s3_endpoint = os.getenv('S3_ENDPOINT', 'http://minio:9000')
s3_access_key = os.getenv('S3_ACCESS_KEY', 'minioadmin')
s3_secret_key = os.getenv('S3_SECRET_KEY', 'minioadmin')

s3_client = boto3.client(
    's3',
    endpoint_url=s3_endpoint,
    aws_access_key_id=s3_access_key,
    aws_secret_access_key=s3_secret_key,
    region_name='us-east-1'
)
BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'avatars')

class UserUpdate(BaseModel):
    full_name: str

class ProfileUpdate(BaseModel):
    financial_goals: str
    risk_tolerance: str
    assets_value: float

class AdviceResponse(BaseModel):
    advice: str

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=User)
def update_user(user_data: UserUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Update user's display name"""
    current_user.full_name = user_data.full_name
    current_user.updated_at = datetime.now(timezone.utc)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user

@router.post("/me/avatar", response_model=User)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Upload and update user's avatar"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")
    
    # Generate unique filename
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    s3_key = f"{current_user.id}/{timestamp}.{file_extension}"
    
    try:
        # Create bucket if it doesn't exist
        try:
            s3_client.head_bucket(Bucket=BUCKET_NAME)
        except:
            s3_client.create_bucket(Bucket=BUCKET_NAME)
        
        # Upload to S3/Minio
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=contents,
            ContentType=file.content_type
        )
        
        # Use proxy URL
        # Assuming the backend is accessible at the same host, we return a relative URL or absolute if needed.
        # Here we construct a path that points to the new get_avatar endpoint.
        # We need an absolute URL because the frontend is on a different port (3000 vs 8000)
        base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        avatar_url = f"{base_url}/users/avatars/{current_user.id}/{timestamp}.{file_extension}"
        
        # Update user record
        current_user.avatar_url = avatar_url
        current_user.updated_at = datetime.now(timezone.utc)
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
        
        return current_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")


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


@router.get("/avatars/{user_id}/{filename}")
async def get_avatar(user_id: str, filename: str):
    """Proxy avatar images from S3"""
    try:
        s3_key = f"{user_id}/{filename}"
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        return StreamingResponse(
            response['Body'].iter_chunks(),
            media_type=response.get('ContentType', 'image/jpeg')
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="Avatar not found")

@router.get("/admin/users", response_model=list[User])
def list_all_users(admin: User = Depends(require_role(UserRole.ADMIN)), session: Session = Depends(get_session)):
    """Admin only: List all users"""
    return session.exec(select(User)).all()
