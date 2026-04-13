#!/usr/bin/env bash

set -euo pipefail

python scripts/prepare_database.py
python scripts/seed.py
exec "$@"
