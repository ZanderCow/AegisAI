#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/infra/docker-compose.e2e.yml"
ENV_FILE="${REPO_ROOT}/infra/.env"
COMPOSE_CMD=(docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}")

export CI="${CI:-true}"

log_step() {
  printf '\n==> %s\n' "$1"
}

cleanup() {
  local exit_code=$?
  trap - EXIT
  set +e
  printf '\n==> Cleaning up e2e test stack\n'
  "${COMPOSE_CMD[@]}" down --volumes --remove-orphans
  exit "${exit_code}"
}

trap cleanup EXIT

log_step "Building e2e test images"
"${COMPOSE_CMD[@]}" build

log_step "Starting shared infrastructure"
"${COMPOSE_CMD[@]}" up -d db chroma



log_step "Starting application infrastructure"
"${COMPOSE_CMD[@]}" up -d backend frontend

e2e_exit=0

log_step "Running E2E tests"
set +e
"${COMPOSE_CMD[@]}" run --rm e2e
e2e_exit=$?
set -e

log_step "Test summary"
printf 'E2E exit code: %s\n' "${e2e_exit}"

if [[ "${e2e_exit}" -ne 0 ]]; then
  exit "${e2e_exit}"
fi

exit 0
