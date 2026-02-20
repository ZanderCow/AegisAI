"""
auth.py
=======
Pydantic schemas for authentication endpoints.

This module defines request and response models for user registration
and login operations.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Schema for user registration request."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        description="User's password (minimum 8 characters)",
        examples=["SecurePass123!"]
    )


class RegisterResponse(BaseModel):
    """Schema for user registration response."""

    user_id: UUID = Field(
        ...,
        description="Unique identifier for the registered user"
    )
    email: EmailStr = Field(
        ...,
        description="User's email address"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the user was created"
    )
    jwt: str = Field(
        ...,
        description="JWT access token for the new user"
    )


class LoginRequest(BaseModel):
    """Schema for user login request."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        description="User's password",
        examples=["SecurePass123!"]
    )


class LoginResponse(BaseModel):
    """Schema for user login response."""

    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    token_type: str = Field(
        default="bearer",
        description="Type of token"
    )

class UserProfileResponse(BaseModel):
    """Schema for user profile response."""

    user_id: UUID = Field(
        ...,
        description="Unique identifier for the user"
    )
    email: EmailStr = Field(
        ...,
        description="User's email address"
    )
    username: str = Field(
        ...,
        description="User's username"
    )
    full_name: str | None = Field(
        default=None,
        description="User's full name"
    )
    is_active: bool = Field(
        ...,
        description="Whether the user account is active"
    )
    created_at: datetime = Field(
        ...,
        description="When the user account was created"
    )
    updated_at: datetime = Field(
        ...,
        description="When the user account was last updated"
    )

class ChangePasswordRequest(BaseModel):
    """Schema for changing password."""
    
    current_password: str = Field(
        ...,
        description="Current password for verification"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (minimum 8 characters)"
    )


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr = Field(
        ...,
        description="Email address for password reset"
    )


class PasswordResetConfirmRequest(BaseModel):
    """Schema for password reset confirmation."""
    
    token: str = Field(
        ...,
        description="Password reset token from email"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (minimum 8 characters)"
    )

class EmailVerificationRequest(BaseModel):
    """Schema for email verification."""
    
    token: str = Field(
        ...,
        description="Email verification token from email"
    )