from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class WebhookConfig(BaseModel):
    url: str
    events: list[str]

@router.post("/configure")
async def configure_webhook(config: WebhookConfig):
    # Logic to save webhook configuration
    return {"status": "configured", "config": config}
