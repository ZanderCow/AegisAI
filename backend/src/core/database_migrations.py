"""Alembic-backed database migration helpers.

This module centralizes the runtime checks and repair paths needed to
interact with Alembic from deployment automation and application startup.
"""
from __future__ import annotations

from collections.abc import Collection
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.database_urls import to_sync_database_url
from src.models.registry import metadata

ALEMBIC_INI_PATH = Path(__file__).resolve().parents[2] / "alembic.ini"
EXPECTED_TABLE_NAMES = frozenset(metadata.tables.keys())


def build_alembic_config(database_url: str) -> Config:
    """Build an Alembic configuration bound to a specific database URL."""
    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option("sqlalchemy.url", to_sync_database_url(database_url))
    return config


def _read_schema_state(sync_connection: object) -> tuple[str | None, set[str]]:
    """Return the current Alembic revision and visible table names."""
    current_revision = MigrationContext.configure(sync_connection).get_current_revision()
    table_names = set(sa_inspect(sync_connection).get_table_names())
    return current_revision, table_names


def _format_table_names(table_names: Collection[str]) -> str:
    """Render table names consistently for operator-facing messages."""
    if not table_names:
        return "(none)"
    return ", ".join(sorted(table_names))


def _read_schema_differences(sync_connection: object) -> list[object]:
    """Return Alembic autogenerate diffs between the database and ORM metadata."""
    migration_context = MigrationContext.configure(
        sync_connection,
        opts={
            "target_metadata": metadata,
            "compare_type": True,
        },
    )
    return compare_metadata(migration_context, metadata)


def repair_unstamped_but_current_schema(database_url: str) -> bool:
    """Stamp head when an existing schema already matches the current metadata.

    This handles environments that were bootstrapped before Alembic-managed
    startup but already contain all application tables. The helper is narrow on
    purpose: it only auto-stamps when every expected table exists and Alembic's
    autogenerate diff reports no remaining schema changes.
    """
    config = build_alembic_config(database_url)
    sync_engine = create_engine(to_sync_database_url(database_url))

    try:
        with sync_engine.begin() as connection:
            current_revision, table_names = _read_schema_state(connection)
            present_app_tables = table_names & EXPECTED_TABLE_NAMES
            missing_tables = EXPECTED_TABLE_NAMES - table_names

            if current_revision is not None or not present_app_tables:
                return False

            if missing_tables:
                raise RuntimeError(
                    "Database schema is partially initialized without an Alembic "
                    "revision stamp. "
                    f"Present app tables: {_format_table_names(present_app_tables)}. "
                    f"Missing app tables: {_format_table_names(missing_tables)}. "
                    "Automatic repair was skipped because the database does not "
                    "match a fully initialized schema."
                )

            schema_differences = _read_schema_differences(connection)
            if schema_differences:
                raise RuntimeError(
                    "Database schema contains all expected tables but does not "
                    "match the current ORM metadata, and Alembic has no revision "
                    "stamp to anchor an upgrade path. Automatic stamping was "
                    f"skipped. Pending schema differences: {schema_differences!r}."
                )

        command.stamp(config, "head")
        return True
    finally:
        sync_engine.dispose()


def repair_stamped_but_incomplete_schema(database_url: str) -> bool:
    """Repair a head-stamped database that is still missing all app tables.

    This is intentionally narrow. It only auto-repairs when Alembic reports the
    current head revision but none of the application tables exist yet. That
    covers interrupted fresh-database bootstraps without making destructive
    guesses about partially migrated or populated schemas.
    """
    config = build_alembic_config(database_url)
    expected_revision = ScriptDirectory.from_config(config).get_current_head()
    sync_engine = create_engine(to_sync_database_url(database_url))

    try:
        with sync_engine.begin() as connection:
            current_revision, table_names = _read_schema_state(connection)
            missing_tables = EXPECTED_TABLE_NAMES - table_names
            present_app_tables = table_names & EXPECTED_TABLE_NAMES

            if current_revision != expected_revision or not missing_tables:
                return False

            if present_app_tables:
                raise RuntimeError(
                    "Database schema is inconsistent: Alembic is stamped at the "
                    "current head revision, but required tables are missing. "
                    f"Present app tables: {_format_table_names(present_app_tables)}. "
                    f"Missing app tables: {_format_table_names(missing_tables)}. "
                    "Automatic repair was skipped because the database appears "
                    "partially migrated."
                )

            connection.exec_driver_sql("DROP TABLE IF EXISTS alembic_version")

        command.upgrade(config, "head")
        return True
    finally:
        sync_engine.dispose()


async def verify_database_schema_current(engine: AsyncEngine, database_url: str) -> None:
    """Fail fast when the connected database is not fully migrated."""
    config = build_alembic_config(database_url)
    expected_revision = ScriptDirectory.from_config(config).get_current_head()

    async with engine.connect() as connection:
        current_revision, table_names = await connection.run_sync(_read_schema_state)

    if current_revision is None:
        raise RuntimeError(
            "Database schema is not initialized. Run `uv run alembic upgrade head` "
            "before starting the API.",
        )

    if current_revision != expected_revision:
        raise RuntimeError(
            "Database schema is out of date. Run `uv run alembic upgrade head` "
            f"before starting the API. Current revision: {current_revision}. "
            f"Expected revision: {expected_revision}.",
        )

    missing_tables = EXPECTED_TABLE_NAMES - table_names
    if missing_tables:
        raise RuntimeError(
            "Database schema revision is marked current, but required tables are "
            "missing. "
            f"Missing app tables: {_format_table_names(missing_tables)}.",
        )
