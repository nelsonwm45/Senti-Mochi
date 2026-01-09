from fastapi import APIRouter
from app.database import engine
from sqlalchemy import text
import redis
import os

router = APIRouter(prefix="/api/v1/health", tags=["health"])

@router.get("/")
async def health_check():
    """Basic liveness check"""
    return {
        "status": "healthy",
        "service": "Finance API"
    }

@router.get("/ready")
async def readiness_check():
    """
    Comprehensive readiness check
    
    Checks:
    - Database connectivity
    - Redis connectivity
    - S3/MinIO connectivity (optional)
    """
    checks = {}
    
    # Check database
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    
    # Check Redis
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    # Check pgvector extension
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
            if result.fetchone():
                checks["pgvector"] = "healthy"
            else:
                checks["pgvector"] = "extension not installed"
    except Exception as e:
        checks["pgvector"] = f"unhealthy: {str(e)}"
    
    # Determine overall status
    all_healthy = all(status == "healthy" for status in checks.values())
    
    return {
        "status": "ready" if all_healthy else "not ready",
        "checks": checks
    }
