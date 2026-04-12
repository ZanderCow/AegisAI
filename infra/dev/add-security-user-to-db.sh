#!/usr/bin/env bash

set -euo pipefail

# Wait for the migrated database before importing application code to hash
# credentials and seed the security account.
echo "Waiting for database connectivity..."
python - <<'PY'
"""Wait for the migrated database to accept connections before seeding."""

import asyncio
import os
import sys
import asyncpg


async def main() -> int:
    raw_database_url = os.environ["DATABASE_URL"]
    database_url = raw_database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    for attempt in range(1, 31):
        try:
            conn = await asyncpg.connect(database_url)
            await conn.close()
            print("Database is reachable.")
            return 0
        except Exception as exc:  # noqa: BLE001 - dev seed script should keep retrying
            print(f"Database check attempt {attempt}/30 failed: {exc}")
            await asyncio.sleep(2)

    print("Database did not become reachable in time.", file=sys.stderr)
    return 1


raise SystemExit(asyncio.run(main()))
PY

# Upsert the deterministic security user used by local compose and Playwright tests.
echo "Seeding dev security user..."
python - <<'PY'
"""Create or update the local development security user."""

import asyncio
import os
import uuid

import asyncpg

from src.security.password import hash_password


async def main() -> int:
    """Upsert the seeded security user in the local Postgres database.

    Returns:
        int: Process exit code, where ``0`` indicates the seed completed.
    """
    raw_database_url = os.environ["DATABASE_URL"]
    database_url = raw_database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    email = os.environ["security_username"]
    password = os.environ["security_password"]
    hashed_password = hash_password(password)

    conn = await asyncpg.connect(database_url)
    try:
        existing = await conn.fetchrow(
            """
            SELECT id
            FROM users
            WHERE email = $1
            """,
            email,
        )

        if existing:
            # Keep credentials and role assignments in sync across container restarts.
            await conn.execute(
                """
                UPDATE users
                SET hashed_password = $2,
                    role = 'security'
                WHERE email = $1
                """,
                email,
                hashed_password,
            )
            print(f"updated security user: {email}")
            return 0

        await conn.execute(
            """
            INSERT INTO users (id, email, hashed_password, role)
            VALUES ($1, $2, $3, 'security')
            """,
            uuid.uuid4(),
            email,
            hashed_password,
        )
    finally:
        await conn.close()

    print(f"created security user: {email}")
    return 0


raise SystemExit(asyncio.run(main()))
PY
