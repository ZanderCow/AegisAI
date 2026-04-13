"""Unit tests for the shared SQLAlchemy model registry."""
from src.models.registry import Base, metadata


def test_model_registry_registers_all_expected_tables() -> None:
    """Verify Alembic and app bootstrap see the same full table set."""
    assert metadata is Base.metadata
    assert set(metadata.tables) == {
        "alarm",
        "conversations",
        "documents",
        "messages",
        "users",
    }
