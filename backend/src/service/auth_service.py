"""Service layer containing business logic for authentication.

This module encapsulates the core business rules for user registration
and login, coordinating between validation schemas, security utilities,
and the database repository.
"""
from fastapi import HTTPException, status
from src.schemas.auth_schema import SignupRequest, LoginRequest, TokenResponse, DuoLoginResponse, DuoCallbackRequest
from src.repo.user_repo import UserRepository
from src.security.password import hash_password, verify_password
from src.security.jwt import create_token, decode_token
from src.security.duo import get_duo_client, DuoException
from src.core.config import settings
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
        new_user = await self.repo.create_user(request.email, hashed_pwd)
        
        logger.info(f"User created successfully: {new_user.id}")
        # 'sub' is the standard subject claim representing the user ID
        token = create_token({"sub": str(new_user.id), "email": new_user.email, "role": new_user.role})
        return TokenResponse(access_token=token, token_type="bearer")

    async def login(self, request: LoginRequest) -> TokenResponse | DuoLoginResponse:
        """Authenticates a user and either issues a JWT or initiates Duo MFA.

        When MFA_ENABLED is False (or Duo is unconfigured) a JWT is returned
        immediately.  When MFA_ENABLED is True, a DuoLoginResponse containing
        the Duo auth URL and a short-lived state token is returned instead.

        Args:
            request (LoginRequest): The validated schema containing login credentials.

        Returns:
            TokenResponse | DuoLoginResponse: A JWT on success, or Duo redirect info.

        Raises:
            HTTPException: 401 if credentials do not match.
            HTTPException: 503 if Duo MFA is enabled but misconfigured.
        """
        logger.info(f"Attempting login for email: {request.email}")
        user = await self.repo.get_by_email(request.email)
        if not user or not verify_password(request.password, user.hashed_password):
            logger.warning(f"Login failed: Invalid credentials for email: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not settings.MFA_ENABLED:
            logger.info(f"MFA disabled — issuing token directly for user: {user.id}")
            token = create_token({"sub": str(user.id), "email": user.email, "role": user.role})
            return TokenResponse(access_token=token, token_type="bearer")

        # MFA path — initiate Duo Universal Prompt flow.
        logger.info(f"MFA enabled — initiating Duo flow for user: {user.id}")
        try:
            duo = get_duo_client()
            duo.health_check()
            state = duo.generate_state()
            auth_url = duo.create_auth_url(user.email, state)
        except DuoException as exc:
            logger.error(f"Duo MFA initiation failed: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MFA service unavailable — please try again later.",
            )

        # Encode user identity + Duo state in a short-lived token so the
        # callback endpoint can verify without server-side session storage.
        state_token = create_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "duo_state": state,
                "type": "mfa_pending",
            },
            expires_minutes=5,
        )
        return DuoLoginResponse(duo_auth_url=auth_url, state_token=state_token)

    async def duo_callback(self, request: DuoCallbackRequest) -> TokenResponse:
        """Completes Duo MFA and issues a full session JWT.

        Decodes the state_token to recover the pending user identity, verifies
        the Duo state matches, then exchanges the Duo code for a result.

        Args:
            request (DuoCallbackRequest): Code, state, and state_token from the callback.

        Returns:
            TokenResponse: A full session JWT on successful MFA verification.

        Raises:
            HTTPException: 401 if the state_token is invalid or the states don't match.
            HTTPException: 401 if Duo rejects the authorization code.
        """
        try:
            payload = decode_token(request.state_token)
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid state token")

        if payload.get("type") != "mfa_pending":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid state token")

        expected_state = payload.get("duo_state")
        if not expected_state or expected_state != request.state:
            logger.warning("Duo state mismatch — possible CSRF attempt")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="State mismatch")

        username = payload.get("email")
        user_id = payload.get("sub")

        try:
            duo = get_duo_client()
            duo.exchange_authorization_code_for_2fa_result(request.duo_code, username)
        except DuoException as exc:
            logger.warning(f"Duo MFA verification failed for {username}: {exc}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA verification failed")

        logger.info(f"Duo MFA passed — issuing token for user: {user_id}")
        token_payload = {"sub": user_id, "email": username}
        if payload.get("role"):
            token_payload["role"] = payload["role"]
        token = create_token(token_payload)
        return TokenResponse(access_token=token, token_type="bearer")
