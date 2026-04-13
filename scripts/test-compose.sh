#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/infra/docker-compose.test.yml"
ENV_FILE="${REPO_ROOT}/infra/.env"
COMPOSE_CMD=(docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}")

log_step() {
  printf '\n==> %s\n' "$1"
}

cleanup() {
  local exit_code=$?
  trap - EXIT
  set +e
  printf '\n==> Cleaning up test stack\n'
  "${COMPOSE_CMD[@]}" down --volumes --remove-orphans
  exit "${exit_code}"
}

trap cleanup EXIT

log_step "Building test images"
"${COMPOSE_CMD[@]}" build backend-test frontend-test

log_step "Starting test infrastructure"
"${COMPOSE_CMD[@]}" up -d db chroma



backend_exit=0
frontend_exit=0

log_step "Running backend tests"
set +e
"${COMPOSE_CMD[@]}" run --rm --no-deps backend-test
backend_exit=$?

log_step "Running frontend tests"
"${COMPOSE_CMD[@]}" run --rm --no-deps frontend-test
frontend_exit=$?
set -e

log_step "Test summary"
printf 'Backend exit code: %s\n' "${backend_exit}"
printf 'Frontend exit code: %s\n' "${frontend_exit}"

if [[ "${backend_exit}" -ne 0 ]]; then
  exit "${backend_exit}"
fi

exit "${frontend_exit}"
