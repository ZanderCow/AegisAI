"""
models.py
=========
SQLAlchemy ORM models for the **Products** domain.

This module defines the ``Product`` table and its columns.  All models inherit
from the shared ``Base`` declared in :pymod:`src.database` so that a single
``Base.metadata`` registry tracks every table in the application.

Column Design Choices
---------------------
* **UUID primary key** – avoids sequential-ID enumeration and works well in
  distributed systems.  The default is generated server-side by PostgreSQL's
  ``gen_random_uuid()`` function.
* **name** – unique index for fast look-ups and to enforce uniqueness at the
  database level.
* **price** – stored as ``Numeric(10, 2)`` for exact decimal arithmetic.
* **created_at / updated_at** – timestamped with time-zone awareness; both
  default to ``now()`` and ``updated_at`` refreshes automatically on every
  ``UPDATE`` statement.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Product(Base):
    """Represents a product stored in the ``products`` table.

    Attributes
    ----------
    id : uuid.UUID
        Primary key generated server-side by PostgreSQL.
    name : str
        The product name (unique, max 200 characters).
    description : str | None
        Optional product description.
    price : Decimal
        Unit price stored with two decimal places.
    created_at : datetime
        Row creation timestamp (set once by the database).
    updated_at : datetime
        Last-modification timestamp (auto-refreshed on every update).
    """

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        comment="Auto-generated UUID primary key.",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False,
        index=True,
        comment="Product name – unique, max 200 chars.",
    )

    description: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        default=None,
        comment="Optional product description.",
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Unit price with two decimal places.",
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
            f"<Product(id={self.id!r}, name={self.name!r}, "
            f"price={self.price!r})>"
        )
