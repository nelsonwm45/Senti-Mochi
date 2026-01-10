from fastapi import APIRouter

router = APIRouter()

@router.get("/zapier/triggers")
async def get_zapier_triggers():
    return {"triggers": ["document_processed", "report_generated"]}
