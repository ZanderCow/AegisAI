"""Prepare the application database before starting the API process.

This script applies Alembic migrations, detects the specific broken state
where the database is stamped at the current revision but the application
tables are missing, and repairs that state before startup continues.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
import sys

from alembic import command
from sqlalchemy.ext.asyncio import create_async_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.database_migrations import (
    build_alembic_config,
    repair_stamped_but_incomplete_schema,
    repair_unstamped_but_current_schema,
    verify_database_schema_current,
)
from src.core.database_urls import load_database_url

logger = logging.getLogger("db-prepare")

if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
    )


async def async_main() -> int:
    """Apply migrations and repair the known pre-Alembic bootstrap failure modes."""
    database_url = load_database_url()
    config = build_alembic_config(database_url)
    engine = create_async_engine(database_url, echo=False)

    try:
        logger.info("Applying Alembic migrations.")
        repaired_unstamped_schema = repair_unstamped_but_current_schema(database_url)
        if repaired_unstamped_schema:
            logger.warning(
                "Detected an existing database schema without an Alembic revision "
                "stamp. Verified the schema matches the current metadata and "
                "stamped the database at the current head revision."
            )
        else:
            command.upgrade(config, "head")

        try:
            await verify_database_schema_current(engine, database_url)
        except RuntimeError as exc:
            repaired = repair_stamped_but_incomplete_schema(database_url)
            if not repaired:
                logger.error("Database preparation failed: %s", exc)
                return 1

            logger.warning(
                "Detected an Alembic-stamped database without the required "
                "application tables. Repaired the revision stamp and re-applied "
                "migrations."
            )
            await verify_database_schema_current(engine, database_url)

        logger.info("Database schema is ready.")
        return 0
    finally:
        await engine.dispose()


def main() -> int:
    """Synchronous wrapper for CLI execution."""
    return asyncio.run(async_main())


if __name__ == "__main__":
    raise SystemExit(main())
