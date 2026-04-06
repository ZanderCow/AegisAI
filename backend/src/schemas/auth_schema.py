"""Pydantic schemas outlining the shapes of API requests and responses.

Schemas act as the Validation layer between external client requests
and internal application Services. They are also parsed by FastAPI
to generate the automatic OpenAPI Swagger UI.
"""
from typing import Literal
from pydantic import BaseModel, EmailStr, Field

UserRoleLiteral = Literal["admin", "security", "it", "hr", "finance"]

class SignupRequest(BaseModel):
    """Schema defining the required JSON payload for user registration."""
    email: EmailStr = Field(description="The user's valid email address.")
    password: str = Field(min_length=8, description="The user's chosen password, containing at least 8 characters.")
    role: UserRoleLiteral = Field(default="it", description="The user's role. Defaults to 'it'.")

class LoginRequest(BaseModel):
    """Schema defining the required JSON payload to obtain a JWT."""
    email: EmailStr = Field(description="The email address registered to the account.")
    password: str = Field(description="The account password in plaintext.")

class TokenResponse(BaseModel):
    """Schema representing the structure of a successful authentication token response."""
    access_token: str = Field(description="The cryptographically signed JWT strings.")
    token_type: str = Field(description="The type of token being returned (usually 'bearer').")
