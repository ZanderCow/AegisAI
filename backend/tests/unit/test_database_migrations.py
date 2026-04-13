"""Unit tests for Alembic runtime helpers."""
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

import src.core.database_migrations as database_migrations

CURRENT_REVISION = "20260413_000002"


def test_build_alembic_config_converts_async_database_urls() -> None:
    """Verify runtime async URLs are converted for Alembic's sync engine."""
    config = database_migrations.build_alembic_config(
        "postgresql+asyncpg://user:pass@localhost:5432/auth_db",
    )

    assert config.config_file_name == str(database_migrations.ALEMBIC_INI_PATH)
    assert (
        config.get_main_option("sqlalchemy.url")
        == "postgresql+psycopg2://user:pass@localhost:5432/auth_db"
    )


@pytest.mark.asyncio
async def test_verify_database_schema_current_accepts_current_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify startup validation passes when the database matches Alembic head."""
    fake_engine = Mock()
    fake_connection = Mock()
    fake_connection.run_sync = AsyncMock(
        return_value=(
            CURRENT_REVISION,
            set(database_migrations.EXPECTED_TABLE_NAMES),
        )
    )
    fake_context_manager = MagicMock()
    fake_context_manager.__aenter__ = AsyncMock(return_value=fake_connection)
    fake_context_manager.__aexit__ = AsyncMock(return_value=None)
    fake_engine.connect.return_value = fake_context_manager

    fake_script_directory = Mock()
    fake_script_directory.get_current_head.return_value = CURRENT_REVISION

    monkeypatch.setattr(
        database_migrations,
        "build_alembic_config",
        Mock(return_value=Mock()),
    )
    monkeypatch.setattr(
        database_migrations.ScriptDirectory,
        "from_config",
        Mock(return_value=fake_script_directory),
    )

    await database_migrations.verify_database_schema_current(
        fake_engine,
        "postgresql+asyncpg://user:pass@localhost:5432/auth_db",
    )


@pytest.mark.asyncio
async def test_verify_database_schema_current_rejects_missing_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify startup validation fails clearly for an unmigrated database."""
    fake_engine = Mock()
    fake_connection = Mock()
    fake_connection.run_sync = AsyncMock(return_value=(None, set()))
    fake_context_manager = MagicMock()
    fake_context_manager.__aenter__ = AsyncMock(return_value=fake_connection)
    fake_context_manager.__aexit__ = AsyncMock(return_value=None)
    fake_engine.connect.return_value = fake_context_manager

    fake_script_directory = Mock()
    fake_script_directory.get_current_head.return_value = CURRENT_REVISION

    monkeypatch.setattr(
        database_migrations,
        "build_alembic_config",
        Mock(return_value=Mock()),
    )
    monkeypatch.setattr(
        database_migrations.ScriptDirectory,
        "from_config",
        Mock(return_value=fake_script_directory),
    )

    with pytest.raises(RuntimeError, match="Database schema is not initialized"):
        await database_migrations.verify_database_schema_current(
            fake_engine,
            "postgresql+asyncpg://user:pass@localhost:5432/auth_db",
        )


@pytest.mark.asyncio
async def test_verify_database_schema_current_rejects_missing_tables_at_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify stamped-but-empty schemas fail with a clear integrity error."""
    fake_engine = Mock()
    fake_connection = Mock()
    fake_connection.run_sync = AsyncMock(
        return_value=(CURRENT_REVISION, {"alembic_version"})
    )
    fake_context_manager = MagicMock()
    fake_context_manager.__aenter__ = AsyncMock(return_value=fake_connection)
    fake_context_manager.__aexit__ = AsyncMock(return_value=None)
    fake_engine.connect.return_value = fake_context_manager

    fake_script_directory = Mock()
    fake_script_directory.get_current_head.return_value = CURRENT_REVISION

    monkeypatch.setattr(
        database_migrations,
        "build_alembic_config",
        Mock(return_value=Mock()),
    )
    monkeypatch.setattr(
        database_migrations.ScriptDirectory,
        "from_config",
        Mock(return_value=fake_script_directory),
    )

    with pytest.raises(RuntimeError, match="required tables are missing"):
        await database_migrations.verify_database_schema_current(
            fake_engine,
            "postgresql+asyncpg://user:pass@localhost:5432/auth_db",
        )


def test_repair_stamped_but_incomplete_schema_repairs_empty_app_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the helper repairs a head-stamped database with no app tables."""
    fake_connection = Mock()
    fake_context_manager = MagicMock()
    fake_context_manager.__enter__ = Mock(return_value=fake_connection)
    fake_context_manager.__exit__ = Mock(return_value=None)

    fake_engine = Mock()
    fake_engine.begin.return_value = fake_context_manager
    fake_engine.dispose = Mock()

    fake_config = Mock()
    fake_script_directory = Mock()
    fake_script_directory.get_current_head.return_value = CURRENT_REVISION
    fake_upgrade = Mock()

    monkeypatch.setattr(database_migrations, "build_alembic_config", Mock(return_value=fake_config))
    monkeypatch.setattr(database_migrations, "create_engine", Mock(return_value=fake_engine))
    monkeypatch.setattr(
        database_migrations.ScriptDirectory,
        "from_config",
        Mock(return_value=fake_script_directory),
    )
    monkeypatch.setattr(
        database_migrations,
        "_read_schema_state",
        Mock(return_value=(CURRENT_REVISION, {"alembic_version"})),
    )
    monkeypatch.setattr(database_migrations.command, "upgrade", fake_upgrade)

    repaired = database_migrations.repair_stamped_but_incomplete_schema(
        "postgresql+asyncpg://user:pass@localhost:5432/auth_db",
    )

    assert repaired is True
    fake_connection.exec_driver_sql.assert_called_once_with("DROP TABLE IF EXISTS alembic_version")
    fake_upgrade.assert_called_once_with(fake_config, "head")
    fake_engine.dispose.assert_called_once()


def test_repair_stamped_but_incomplete_schema_refuses_partial_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the helper refuses automatic repair for partial app schemas."""
    fake_connection = Mock()
    fake_context_manager = MagicMock()
    fake_context_manager.__enter__ = Mock(return_value=fake_connection)
    fake_context_manager.__exit__ = Mock(return_value=None)

    fake_engine = Mock()
    fake_engine.begin.return_value = fake_context_manager
    fake_engine.dispose = Mock()

    fake_config = Mock()
    fake_script_directory = Mock()
    fake_script_directory.get_current_head.return_value = CURRENT_REVISION
    fake_upgrade = Mock()

    monkeypatch.setattr(database_migrations, "build_alembic_config", Mock(return_value=fake_config))
    monkeypatch.setattr(database_migrations, "create_engine", Mock(return_value=fake_engine))
    monkeypatch.setattr(
        database_migrations.ScriptDirectory,
        "from_config",
        Mock(return_value=fake_script_directory),
    )
    monkeypatch.setattr(
        database_migrations,
        "_read_schema_state",
        Mock(return_value=(CURRENT_REVISION, {"alembic_version", "users"})),
    )
    monkeypatch.setattr(database_migrations.command, "upgrade", fake_upgrade)

    with pytest.raises(RuntimeError, match="partially migrated"):
        database_migrations.repair_stamped_but_incomplete_schema(
            "postgresql+asyncpg://user:pass@localhost:5432/auth_db",
        )

    fake_connection.exec_driver_sql.assert_not_called()
    fake_upgrade.assert_not_called()
    fake_engine.dispose.assert_called_once()


def test_repair_unstamped_but_current_schema_stamps_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify fully initialized unstamped schemas are stamped at head."""
    fake_connection = Mock()
    fake_context_manager = MagicMock()
    fake_context_manager.__enter__ = Mock(return_value=fake_connection)
    fake_context_manager.__exit__ = Mock(return_value=None)

    fake_engine = Mock()
    fake_engine.begin.return_value = fake_context_manager
    fake_engine.dispose = Mock()

    fake_config = Mock()
    fake_stamp = Mock()

    monkeypatch.setattr(database_migrations, "build_alembic_config", Mock(return_value=fake_config))
    monkeypatch.setattr(database_migrations, "create_engine", Mock(return_value=fake_engine))
    monkeypatch.setattr(
        database_migrations,
        "_read_schema_state",
        Mock(return_value=(None, set(database_migrations.EXPECTED_TABLE_NAMES))),
    )
    monkeypatch.setattr(
        database_migrations,
        "_read_schema_differences",
        Mock(return_value=[]),
    )
    monkeypatch.setattr(database_migrations.command, "stamp", fake_stamp)

    repaired = database_migrations.repair_unstamped_but_current_schema(
        "postgresql+asyncpg://user:pass@localhost:5432/auth_db",
    )

    assert repaired is True
    fake_stamp.assert_called_once_with(fake_config, "head")
    fake_engine.dispose.assert_called_once()


def test_repair_unstamped_but_current_schema_refuses_partial_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify partially initialized unstamped schemas are not auto-stamped."""
    fake_connection = Mock()
    fake_context_manager = MagicMock()
    fake_context_manager.__enter__ = Mock(return_value=fake_connection)
    fake_context_manager.__exit__ = Mock(return_value=None)

    fake_engine = Mock()
    fake_engine.begin.return_value = fake_context_manager
    fake_engine.dispose = Mock()

    monkeypatch.setattr(database_migrations, "build_alembic_config", Mock(return_value=Mock()))
    monkeypatch.setattr(database_migrations, "create_engine", Mock(return_value=fake_engine))
    monkeypatch.setattr(
        database_migrations,
        "_read_schema_state",
        Mock(return_value=(None, {"users"})),
    )
    monkeypatch.setattr(database_migrations.command, "stamp", Mock())

    with pytest.raises(RuntimeError, match="partially initialized without an Alembic revision stamp"):
        database_migrations.repair_unstamped_but_current_schema(
            "postgresql+asyncpg://user:pass@localhost:5432/auth_db",
        )

    database_migrations.command.stamp.assert_not_called()
    fake_engine.dispose.assert_called_once()


def test_repair_unstamped_but_current_schema_refuses_schema_with_pending_diffs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify auto-stamping is skipped when the unstamped schema differs from metadata."""
    fake_connection = Mock()
    fake_context_manager = MagicMock()
    fake_context_manager.__enter__ = Mock(return_value=fake_connection)
    fake_context_manager.__exit__ = Mock(return_value=None)

    fake_engine = Mock()
    fake_engine.begin.return_value = fake_context_manager
    fake_engine.dispose = Mock()

    monkeypatch.setattr(database_migrations, "build_alembic_config", Mock(return_value=Mock()))
    monkeypatch.setattr(database_migrations, "create_engine", Mock(return_value=fake_engine))
    monkeypatch.setattr(
        database_migrations,
        "_read_schema_state",
        Mock(return_value=(None, set(database_migrations.EXPECTED_TABLE_NAMES))),
    )
    monkeypatch.setattr(
        database_migrations,
        "_read_schema_differences",
        Mock(return_value=[("add_column", None, "users", "full_name")]),
    )
    monkeypatch.setattr(database_migrations.command, "stamp", Mock())

    with pytest.raises(RuntimeError, match="does not match the current ORM metadata"):
        database_migrations.repair_unstamped_but_current_schema(
            "postgresql+asyncpg://user:pass@localhost:5432/auth_db",
        )

    database_migrations.command.stamp.assert_not_called()
    fake_engine.dispose.assert_called_once()
