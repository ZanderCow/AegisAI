"""
schemas.py
==========
Pydantic v2 schemas for **User** request / response validation.

These schemas form the public contract of the Users API.  They are
intentionally separate from the SQLAlchemy model so that internal
database details never leak into API responses and incoming payloads
are validated before they reach the service layer.

Schemas
-------
``UserCreate``
    Validates the JSON body sent by clients when creating a new user.

``UserRead``
    Serialises a ``User`` ORM instance into a JSON-friendly response.
    Uses ``model_config = ConfigDict(from_attributes=True)`` so that
    Pydantic can read values directly from SQLAlchemy model attributes.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Request Schemas ─────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    """Schema for the **POST /users/** request body.

    Attributes
    ----------
    email : EmailStr
        A valid email address (validated by Pydantic's ``EmailStr``).
    username : str
        A display name between 3 and 50 characters.
    full_name : str | None
        Optional full name, up to 100 characters.
    """

    email: EmailStr = Field(
        ...,
        description="A valid email address for the new user.",
        examples=["alice@example.com"],
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="A unique display name (3–50 characters).",
        examples=["alice_wonder"],
    )
    full_name: str | None = Field(
        default=None,
        max_length=100,
        description="Optional full name of the user.",
        examples=["Alice Wonderland"],
    )


# ── Response Schemas ────────────────────────────────────────────────────────


class UserRead(BaseModel):
    """Schema returned by every endpoint that exposes user data.

    Attributes
    ----------
    id : uuid.UUID
        The user's unique identifier.
    email : str
        The user's email address.
    username : str
        The user's display name.
    full_name : str | None
        The user's full name (may be ``None``).
    is_active : bool
        Whether the account is active.
    created_at : datetime
        When the account was created.
    updated_at : datetime
        When the account was last modified.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        ...,
        description="Auto-generated unique identifier.",
    )
    email: str = Field(
        ...,
        description="The user's email address.",
    )
    username: str = Field(
        ...,
        description="The user's display name.",
    )
    full_name: str | None = Field(
        default=None,
        description="The user's full name.",
    )
    is_active: bool = Field(
        ...,
        description="Whether the account is active.",
    )
    created_at: datetime = Field(
        ...,
        description="Row creation timestamp.",
    )
    updated_at: datetime = Field(
        ...,
        description="Last-modification timestamp.",
    )