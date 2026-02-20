from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from repo.user_repository import UserRepository
from service.user_service import UserService

router = APIRouter()


def _make_service(db: AsyncSession) -> UserService:
    return UserService(UserRepository(db))


@router.post("/signup", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user and return a JWT access token."""
    service = _make_service(db)
    user, token = await service.register_user(body.email, body.password)
    return RegisterResponse(
        user_id=user.id,
        email=user.email,
        created_at=user.created_at,
        jwt=token,
    )


@router.post("/login/access-token", response_model=LoginResponse)
async def login_access_token(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate a user and return a JWT access token."""
    service = _make_service(db)
    token = await service.login_user(body.email, body.password)
    return LoginResponse(access_token=token)
