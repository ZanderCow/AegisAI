#!/bin/sh
set -eu

FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-http://frontend:5173}"
SELENIUM_REMOTE_URL="${SELENIUM_REMOTE_URL:-http://selenium:4444/wd/hub}"

wait_for_url() {
  url="$1"
  name="$2"
  max_attempts="${3:-60}"
  attempt=1

  while [ "$attempt" -le "$max_attempts" ]; do
    if python - <<PY
import urllib.request
import sys

url = "$url"
try:
    with urllib.request.urlopen(url, timeout=3) as resp:
        sys.exit(0 if 200 <= resp.status < 500 else 1)
except Exception:
    sys.exit(1)
PY
    then
      echo "$name is reachable at $url"
      return 0
    fi

    echo "Waiting for $name at $url ($attempt/$max_attempts)..."
    attempt=$((attempt + 1))
    sleep 2
  done

  echo "Timed out waiting for $name at $url"
  return 1
}

wait_for_url "$SELENIUM_REMOTE_URL/status" "selenium"
wait_for_url "$FRONTEND_BASE_URL" "frontend base url"

pytest -v tests/test_auth_selenium.py
