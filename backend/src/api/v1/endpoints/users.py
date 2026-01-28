from typing import Any
from fastapi import APIRouter, Depends
from src.schemas.users import UserResponse
from src.api.deps import get_current_user
from src.models.user_model import User

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user
