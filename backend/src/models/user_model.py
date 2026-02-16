# user_model.py



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
    hashed_password : str
        The user's hashed password.
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

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hashed password string.",
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
