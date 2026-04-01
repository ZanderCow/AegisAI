#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

cleanup() {
  rm -rf "$ROOT_DIR/.railway"
}

trap cleanup EXIT

CREATE_MISSING_SERVICES="${INPUT_CREATE_MISSING_SERVICES:-no}"
RAILWAY_POSTGRES_SERVICE="${RAILWAY_POSTGRES_SERVICE:-Postgres}"
BACKEND_ALGORITHM="${BACKEND_ALGORITHM:-HS256}"
CHROMA_COLLECTION_NAME="${CHROMA_COLLECTION_NAME:-rag_documents}"
MOCK_PROVIDER_RESPONSES="${MOCK_PROVIDER_RESPONSES:-false}"
MOCK_PROVIDER_RESPONSES_LOWER="${MOCK_PROVIDER_RESPONSES,,}"

declare -a CREATED_SERVICES=()

log() {
  printf '%s\n' "$*"
}

notice() {
  printf '::notice::%s\n' "$*"
}

warn() {
  printf '::warning::%s\n' "$*"
}

fail() {
  printf '::error::%s\n' "$*" >&2
  exit 1
}

add_summary() {
  if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    printf '%s\n' "$*" >> "$GITHUB_STEP_SUMMARY"
  fi
}

require_value() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    fail "Missing required GitHub secret: ${name}"
  fi
}

require_main_branch() {
  if [[ "${GITHUB_REF_NAME:-}" != "main" ]]; then
    fail "This workflow only deploys from main. Open the workflow on the main branch before running it."
  fi
}

validate_inputs() {
  require_value "RAILWAY_TOKEN"
  require_value "RAILWAY_PROJECT"
  require_value "RAILWAY_ENVIRONMENT"
  require_value "RAILWAY_BACKEND_SERVICE"
  require_value "RAILWAY_FRONTEND_SERVICE"
  require_value "RAILWAY_CHROMA_SERVICE"
  require_value "BACKEND_SECRET_KEY"

  if [[ "$MOCK_PROVIDER_RESPONSES_LOWER" != "true" ]] \
    && [[ -z "${GROQ_API_KEY:-}" ]] \
    && [[ -z "${GEMINI_API_KEY:-}" ]] \
    && [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
    fail "Set at least one of GROQ_API_KEY, GEMINI_API_KEY, or DEEPSEEK_API_KEY, or set MOCK_PROVIDER_RESPONSES=true."
  fi
}

reference_var() {
  local namespace="$1"
  local key="$2"
  printf '${{%s.%s}}' "$namespace" "$key"
}

https_reference_var() {
  local namespace="$1"
  local key="$2"
  printf 'https://${{%s.%s}}' "$namespace" "$key"
}

link_project() {
  railway link \
    --project "$RAILWAY_PROJECT" \
    --environment "$RAILWAY_ENVIRONMENT" \
    --json >/dev/null
}

service_exists() {
  local service="$1"

  railway service status \
    --service "$service" \
    --environment "$RAILWAY_ENVIRONMENT" \
    --json >/dev/null 2>&1
}

create_empty_service() {
  local service="$1"

  notice "Creating missing Railway service: ${service}"
  railway add --service "$service" --json >/dev/null
  CREATED_SERVICES+=("$service")
  link_project
}

attach_chroma_volume() {
  notice "Attaching a persistent Railway volume to Chroma at /data."
  railway volume add \
    --service "$RAILWAY_CHROMA_SERVICE" \
    --environment "$RAILWAY_ENVIRONMENT" \
    --mount-path /data \
    --json >/dev/null
}

create_postgres_service() {
  notice "Creating missing Railway managed Postgres service."
  railway add --database postgres --json >/dev/null
  CREATED_SERVICES+=("$RAILWAY_POSTGRES_SERVICE")
  link_project

  if ! service_exists "$RAILWAY_POSTGRES_SERVICE"; then
    warn "A managed Postgres service was created, but it was not found at the expected name '$RAILWAY_POSTGRES_SERVICE'. Set the RAILWAY_POSTGRES_SERVICE secret to the actual Railway database service name before the next run."
  fi
}

ensure_named_service() {
  local service="$1"

  if service_exists "$service"; then
    notice "Using existing Railway service: ${service}"
    return
  fi

  if [[ "$CREATE_MISSING_SERVICES" != "yes" ]]; then
    fail "Railway service '${service}' does not exist. Re-run this workflow with create_missing_services=yes to bootstrap it."
  fi

  create_empty_service "$service"
}

ensure_chroma_service() {
  if service_exists "$RAILWAY_CHROMA_SERVICE"; then
    notice "Using existing Railway service: ${RAILWAY_CHROMA_SERVICE}"
    return
  fi

  if [[ "$CREATE_MISSING_SERVICES" != "yes" ]]; then
    fail "Railway service '${RAILWAY_CHROMA_SERVICE}' does not exist. Re-run this workflow with create_missing_services=yes to bootstrap it."
  fi

  create_empty_service "$RAILWAY_CHROMA_SERVICE"
  attach_chroma_volume
}

ensure_postgres_service() {
  if service_exists "$RAILWAY_POSTGRES_SERVICE"; then
    notice "Using existing Railway Postgres service: ${RAILWAY_POSTGRES_SERVICE}"
    return
  fi

  if [[ "$CREATE_MISSING_SERVICES" != "yes" ]]; then
    fail "Railway Postgres service '${RAILWAY_POSTGRES_SERVICE}' does not exist. Re-run this workflow with create_missing_services=yes to create it, or update the RAILWAY_POSTGRES_SERVICE secret."
  fi

  create_postgres_service

  # Managed databases can take a bit to finish provisioning before dependent
  # services can connect successfully on their first boot.
  notice "Waiting briefly for Railway Postgres to finish provisioning."
  sleep 60
}

set_service_variables() {
  local service="$1"
  shift

  railway variable set \
    --service "$service" \
    --environment "$RAILWAY_ENVIRONMENT" \
    --skip-deploys \
    "$@" >/dev/null
}

configure_chroma() {
  set_service_variables \
    "$RAILWAY_CHROMA_SERVICE" \
    "PORT=8000"
}

configure_backend() {
  local chroma_host
  local database_url

  chroma_host="$(reference_var "$RAILWAY_CHROMA_SERVICE" "RAILWAY_PRIVATE_DOMAIN")"
  database_url="$(reference_var "$RAILWAY_POSTGRES_SERVICE" "DATABASE_URL")"

  set_service_variables \
    "$RAILWAY_BACKEND_SERVICE" \
    "PORT=8000" \
    "DATABASE_URL=$database_url" \
    "SECRET_KEY=$BACKEND_SECRET_KEY" \
    "ALGORITHM=$BACKEND_ALGORITHM" \
    "ENVIRONMENT=production" \
    "MOCK_PROVIDER_RESPONSES=$MOCK_PROVIDER_RESPONSES_LOWER" \
    "GROQ_API_KEY=${GROQ_API_KEY:-}" \
    "GEMINI_API_KEY=${GEMINI_API_KEY:-}" \
    "DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}" \
    "CHROMA_HOST=$chroma_host" \
    "CHROMA_PORT=8000" \
    "CHROMA_SSL=false" \
    "CHROMA_COLLECTION_NAME=$CHROMA_COLLECTION_NAME"
}

configure_frontend() {
  local api_url

  api_url="$(https_reference_var "$RAILWAY_BACKEND_SERVICE" "RAILWAY_PUBLIC_DOMAIN")"

  set_service_variables \
    "$RAILWAY_FRONTEND_SERVICE" \
    "PORT=80" \
    "VITE_API_URL=$api_url"
}

deploy_path() {
  local service="$1"
  local path="$2"

  log "Deploying ${service} from ${path}"
  railway up "$path" \
    --path-as-root \
    --ci \
    --service "$service" \
    --environment "$RAILWAY_ENVIRONMENT"
}

ensure_public_domain() {
  local service="$1"
  local port="$2"

  railway domain \
    --service "$service" \
    --port "$port" \
    --json >/dev/null
}

write_summary() {
  add_summary "## Railway deploy"
  add_summary ""
  add_summary "- Branch: \`main\`"
  add_summary "- Bootstrap missing services: \`${CREATE_MISSING_SERVICES}\`"
  add_summary "- Deploy order: \`chroma -> backend -> frontend\`"

  if [[ ${#CREATED_SERVICES[@]} -gt 0 ]]; then
    add_summary "- Services created on this run: \`${CREATED_SERVICES[*]}\`"
  else
    add_summary "- Services created on this run: none"
  fi

  add_summary ""
  add_summary "Backend note: this workflow ensures a public Railway domain for the backend so the frontend can bake \`VITE_API_URL\` at build time. Treat that as a temporary compromise and move toward a more private/internal setup later."

  if [[ "${RAILWAY_POSTGRES_SERVICE:-}" == "Postgres" ]]; then
    add_summary "Postgres note: the workflow assumes the managed Railway database service is named \`Postgres\` unless you set the \`RAILWAY_POSTGRES_SERVICE\` secret."
  fi
}

main() {
  require_main_branch
  validate_inputs
  link_project

  ensure_postgres_service
  ensure_chroma_service
  ensure_named_service "$RAILWAY_BACKEND_SERVICE"
  ensure_named_service "$RAILWAY_FRONTEND_SERVICE"

  configure_chroma
  deploy_path "$RAILWAY_CHROMA_SERVICE" "chroma"

  configure_backend
  deploy_path "$RAILWAY_BACKEND_SERVICE" "backend"

  notice "Ensuring the backend has a Railway-provided public domain."
  ensure_public_domain "$RAILWAY_BACKEND_SERVICE" "8000"

  configure_frontend
  deploy_path "$RAILWAY_FRONTEND_SERVICE" "frontend"

  notice "Ensuring the frontend has a Railway-provided public domain."
  ensure_public_domain "$RAILWAY_FRONTEND_SERVICE" "80"

  write_summary
}

main "$@"
