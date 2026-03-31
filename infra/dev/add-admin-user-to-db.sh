#!/usr/bin/env bash

set -euo pipefail

echo "Waiting for backend health endpoint..."
python - <<'PY'
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

echo "Seeding dev admin user..."
python - <<'PY'
import asyncio
import os
import sys
import uuid

import asyncpg

from src.security.password import hash_password


async def main() -> int:
    raw_database_url = os.environ["DATABASE_URL"]
    database_url = raw_database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    email = os.environ["ADMIN_EMAIL"]
    password = os.environ["ADMIN_PASSWORD"]

    conn = await asyncpg.connect(database_url)
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO users (id, email, hashed_password)
            VALUES ($1, $2, $3)
            ON CONFLICT (email) DO NOTHING
            RETURNING id
            """,
            uuid.uuid4(),
            email,
            hash_password(password),
        )
    finally:
        await conn.close()

    if row is None:
        print("user already exists")
        return 0

    print(f"created admin user: {email}")
    return 0


raise SystemExit(asyncio.run(main()))
PY
