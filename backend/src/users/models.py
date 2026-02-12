"""
models.py
=========
SQLAlchemy ORM models for the **Users** domain.

This module defines the ``User`` table and its columns.  All models inherit
from the shared ``Base`` declared in :pymod:`src.database` so that a single
``Base.metadata`` registry tracks every table in the application.

Column Design Choices
---------------------
* **UUID primary key** – avoids sequential-ID enumeration and works well in
  distributed systems.  The default is generated server-side by PostgreSQL's
  ``gen_random_uuid()`` function.
* **email / username** – each has a unique index for fast look-ups and to
  enforce uniqueness at the database level.
* **created_at / updated_at** – timestamped with time-zone awareness; both
  default to ``now()`` and ``updated_at`` refreshes automatically on every
  ``UPDATE`` statement.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class User(Base):
    """Represents an application user stored in the ``users`` table.

    Attributes
    ----------
    id : uuid.UUID
        Primary key generated server-side by PostgreSQL.
    email : str
        The user's email address (unique, max 320 characters per RFC 5321).
    username : str
        A short display name (unique, max 50 characters).
    full_name : str | None
        Optional legal / display name.
    is_active : bool
        Soft-delete flag; ``True`` by default.
    created_at : datetime
        Row creation timestamp (set once by the database).
    updated_at : datetime
        Last-modification timestamp (auto-refreshed on every update).
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        comment="Auto-generated UUID primary key.",
    )

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address – unique, max 320 chars (RFC 5321).",
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Short display name – unique, max 50 chars.",
    )

    full_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
        comment="Optional full / display name.",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        comment="Soft-delete flag; True means the account is active.",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Row creation timestamp (set once by the database).",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last-modification timestamp (auto-refreshed on update).",
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id!r}, username={self.username!r}, "
            f"email={self.email!r})>"
        )