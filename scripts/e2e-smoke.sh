#!/bin/sh
set -eu

BACKEND_URL="${BACKEND_URL:-http://backend:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://frontend:5173}"

wait_for_url() {
  url="$1"
  name="$2"
  max_attempts="${3:-40}"
  attempt=1

  while [ "$attempt" -le "$max_attempts" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "$name is reachable at $url"
      return 0
    fi

    echo "Waiting for $name ($attempt/$max_attempts)..."
    attempt=$((attempt + 1))
    sleep 2
  done

  echo "Timed out waiting for $name at $url"
  return 1
}

wait_for_url "$BACKEND_URL/api/v1/health/" "backend"
wait_for_url "$FRONTEND_URL" "frontend"

backend_health="$(curl -fsS "$BACKEND_URL/api/v1/health/")"
echo "$backend_health" | grep -q '"status":"ok"'

echo "Backend health response: $backend_health"

frontend_status="$(curl -fsS -o /tmp/frontend.html -w '%{http_code}' "$FRONTEND_URL/login")"
if [ "$frontend_status" != "200" ]; then
  echo "Expected frontend /login to return HTTP 200, got $frontend_status"
  exit 1
fi

grep -qi '<title>' /tmp/frontend.html

echo "E2E smoke checks passed."
