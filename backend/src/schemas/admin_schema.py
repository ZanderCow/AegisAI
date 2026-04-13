"""Validation schemas for admin user-management endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from src.schemas.auth_schema import UserRoleLiteral


class AdminUserOut(BaseModel):
    """User payload rendered by the admin user-management table."""

    id: str = Field(description="The user's unique identifier.")
    full_name: str | None = Field(default=None, description="The user's display name.")
    email: EmailStr = Field(description="The user's email address.")
    role: UserRoleLiteral = Field(description="The user's current role.")
    created_at: datetime = Field(description="When the user record was created.")
    last_login: datetime | None = Field(default=None, description="When the user last authenticated.")


class AdminUserRoleUpdateRequest(BaseModel):
    """Request body for updating a user's role."""

    role: UserRoleLiteral = Field(description="The new role to assign to the user.")
