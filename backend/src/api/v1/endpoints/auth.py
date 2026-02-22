from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from src.repo.user_repository import UserRepository
from src.service.user_service import UserService
from src.core.logger import get_logger

auth_logger = get_logger("auth")
router = APIRouter()


def _make_service(db: AsyncSession) -> UserService:
    return UserService(UserRepository(db))


@router.post("/signup", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user and return a JWT access token."""
    auth_logger.info("[AUTH][ROUTER] POST /auth/signup endpoint hit")
    auth_logger.info("[AUTH][VALIDATION] Incoming request body validated successfully")
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
    auth_logger.info("[AUTH][ROUTER] POST /auth/login/access-token endpoint hit")
    auth_logger.info("[AUTH][VALIDATION] Incoming request body validated successfully")
    service = _make_service(db)
    token = await service.login_user(body.email, body.password)
    return LoginResponse(access_token=token)
