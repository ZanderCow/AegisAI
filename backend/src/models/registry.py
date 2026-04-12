"""Central ORM model registry for metadata consumers.

This module imports every SQLAlchemy model so that application startup,
Alembic autogeneration, and tests all operate on the same complete
``Base.metadata`` collection.
"""
from src.models.user_model import Base
from src.models import conversation_model as _conversation_model  # noqa: F401
from src.models import document_model as _document_model  # noqa: F401
from src.models import flagged_event_model as _flagged_event_model  # noqa: F401

metadata = Base.metadata

__all__ = ["Base", "metadata"]
