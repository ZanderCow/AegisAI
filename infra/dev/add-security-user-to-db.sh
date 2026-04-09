#!/usr/bin/env bash

set -euo pipefail

# Wait for the backend container before importing application code to hash
# credentials and seed the security account.
echo "Waiting for backend health endpoint..."
python - <<'PY'
"""Wait for the backend service to report healthy before seeding users."""

import os
import sys
import time
import urllib.error
import urllib.request

health_url = os.environ.get("BACKEND_HEALTH_URL", "http://backend:8000/health")

for attempt in range(1, 31):
    try:
        with urllib.request.urlopen(health_url, timeout=5) as response:
            if response.status == 200:
                print("Backend is healthy.")
                sys.exit(0)
    except Exception as exc:  # noqa: BLE001 - dev seed script should keep retrying
        print(f"Health check attempt {attempt}/30 failed: {exc}")
    time.sleep(2)

print("Backend did not become healthy in time.", file=sys.stderr)
sys.exit(1)
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
