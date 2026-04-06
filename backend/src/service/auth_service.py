"""Service layer containing business logic for authentication.

This module encapsulates the core business rules for user registration
and login, coordinating between validation schemas, security utilities,
and the database repository.
"""
from fastapi import HTTPException, status
from src.schemas.auth_schema import SignupRequest, LoginRequest, TokenResponse
from src.repo.user_repo import UserRepository
from src.security.password import hash_password, verify_password
from src.security.jwt import create_token
from src.core.logger import get_logger

logger = get_logger("AUTH_SERVICE")

class AuthService:
    """Service layer holding all authentication business logic.
    
    Attributes:
        repo (UserRepository): The injected repository for database access.
    """
    def __init__(self, repo: UserRepository):
        """Initializes the service with a database repository instance."""
        self.repo = repo

    async def signup(self, request: SignupRequest) -> TokenResponse:
        """Orchestrates the creation of a new user account.
        
        Checks if the requested email is already in use. If it is available,
        it hashes the provided password, persists the user to the database,
        and generates a secure JWT for immediate authentication.
        
        Args:
            request (SignupRequest): The validated Pydantic schema containing user details.
            
        Returns:
            TokenResponse: A schema containing the newly generated JWT access token.
            
        Raises:
            HTTPException: With a 400 Bad Request if the email is already registered.
        """
        logger.info(f"Attempting signup for email: {request.email}")
        existing_user = await self.repo.get_by_email(request.email)
        if existing_user:
            logger.warning(f"Signup failed: Email already registered ({request.email})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        hashed_pwd = hash_password(request.password)
        new_user = await self.repo.create_user(request.email, hashed_pwd, role=request.role)

        logger.info(f"User created successfully: {new_user.id}")
        # 'sub' is the standard subject claim representing the user ID
        token = create_token({"sub": str(new_user.id), "email": new_user.email, "role": new_user.role})
        return TokenResponse(access_token=token, token_type="bearer")

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticates a user and issues a JWT token.
        
        Retrieves the user by email and compares the provided plaintext password
        with the stored hash. If successful, generates an access token.
        
        Args:
            request (LoginRequest): The validated schema containing login credentials.
            
        Returns:
            TokenResponse: A schema containing a valid JWT access token.
            
        Raises:
            HTTPException: With a 401 Unauthorized if the credentials do not match.
        """
        logger.info(f"Attempting login for email: {request.email}")
        user = await self.repo.get_by_email(request.email)
        if not user or not verify_password(request.password, user.hashed_password):
            logger.warning(f"Login failed: Invalid credentials for email: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
            
        logger.info(f"Login successful for user: {user.id}")
        token = create_token({"sub": str(user.id), "email": user.email, "role": user.role})
        return TokenResponse(access_token=token, token_type="bearer")
