from fastapi import APIRouter
from src.core.db import init_db

router = APIRouter()

@router.get("/")
async def health_check():
    """
    Health check logic.
    """
    return {"status": "ok", "message": "API is healthy"}
