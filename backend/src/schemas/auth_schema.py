"""Pydantic schemas outlining the shapes of API requests and responses.

Schemas act as the Validation layer between external client requests
and internal application Services. They are also parsed by FastAPI
to generate the automatic OpenAPI Swagger UI.
"""
from pydantic import BaseModel, EmailStr, Field

class SignupRequest(BaseModel):
    """Schema defining the required JSON payload for user registration."""
    email: EmailStr = Field(description="The user's valid email address.")
    password: str = Field(min_length=8, description="The user's chosen password, containing at least 8 characters.")

class LoginRequest(BaseModel):
    """Schema defining the required JSON payload to obtain a JWT."""
    email: EmailStr = Field(description="The email address registered to the account.")
    password: str = Field(description="The account password in plaintext.")

class TokenResponse(BaseModel):
    """Schema representing the structure of a successful authentication token response."""
    access_token: str = Field(description="The cryptographically signed JWT strings.")
    token_type: str = Field(description="The type of token being returned (usually 'bearer').")

class DuoLoginResponse(BaseModel):
    """Returned instead of a token when Duo MFA is required.

    The frontend must store the state_token, then redirect the user to duo_auth_url.
    After Duo authenticates the user it redirects back to the configured redirect URI
    where the frontend exchanges the code for a real JWT.
    """
    mfa_required: bool = Field(default=True)
    duo_auth_url: str = Field(description="The Duo-hosted page the user must visit to complete MFA.")
    state_token: str = Field(description="Short-lived JWT encoding the pending user identity and Duo state.")

class DuoCallbackRequest(BaseModel):
    """Payload sent by the frontend after Duo redirects back."""
    duo_code: str = Field(description="The authorization code returned by Duo in the callback URL.")
    state: str = Field(description="The state value returned by Duo in the callback URL.")
    state_token: str = Field(description="The state_token issued by the initial login response.")
