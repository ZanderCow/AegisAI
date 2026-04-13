"""HTTP router API endpoints mapping for authentication.

This module acts strictly as the router (controller) layer, accepting
HTTP calls and transferring the payload cleanly to the `AuthService`.
No business logic or database queries should reside here.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.auth_schema import SignupRequest, LoginRequest, TokenResponse, DuoLoginResponse, DuoCallbackRequest
from src.repo.user_repo import UserRepository
from src.service.auth_service import AuthService
from src.core.logger import get_logger

logger = get_logger("AUTH_API")

router = APIRouter(prefix="/auth", tags=["auth"])

def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency injection wrapper factory for the AuthService layer.
    
    Args:
        session (AsyncSession): The injected database session dependency.
        
    Returns:
        AuthService: An initialized instance of the AuthService.
    """
    return AuthService(UserRepository(session))

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, service: AuthService = Depends(get_auth_service)):
    """Register a new user in the system.
    
    This endpoint accepts an email and password to create a new user profile.
    It delegates validation semantics via dependency injection and business
    rules over to the `AuthService`.
    """
    logger.info(f"Received signup request for {request.email}")
    return await service.signup(request)

@router.post("/login", response_model=TokenResponse | DuoLoginResponse, status_code=status.HTTP_200_OK)
async def login(request: LoginRequest, service: AuthService = Depends(get_auth_service)):
    """Authenticate and obtain an access token.

    When MFA is disabled, returns a JWT directly (TokenResponse).
    When MFA is enabled, returns a Duo auth URL and state token (DuoLoginResponse)
    that the client must use to complete the second factor before a JWT is issued.
    """
    logger.info(f"Received login request for {request.email}")
    return await service.login(request)

@router.post("/duo/callback", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def duo_callback(request: DuoCallbackRequest, service: AuthService = Depends(get_auth_service)):
    """Complete Duo MFA and obtain a session JWT.

    Called by the frontend after Duo redirects back with a code and state.
    Verifies the Duo authorization code and, on success, issues a full JWT.
    """
    logger.info("Received Duo MFA callback")
    return await service.duo_callback(request)
