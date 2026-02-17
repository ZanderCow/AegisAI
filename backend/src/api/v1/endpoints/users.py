from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def read_user_me():
    """Get current user. (Not implemented)"""
    return {"message": "Not implemented"}
