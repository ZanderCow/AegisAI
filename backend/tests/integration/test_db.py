"""
Integration test for database connectivity.

This test requires a running Postgres instance reachable at the URL
configured in DATABASE_URL (or the default in config.py). It is expected
to fail when no database is available.
"""

import pytest
from sqlalchemy import text

from src.core.db import engine


class TestDatabase:
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Verify that the engine can open a connection and execute a simple query."""
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.scalar()
        assert row == 1

