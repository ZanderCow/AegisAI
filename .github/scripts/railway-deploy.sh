#!/usr/bin/env bash
#
# Deploy AegisAI services to Railway from GitHub Actions.
#
# This script is intentionally conservative:
# - it requires an account/workspace-scoped Railway API token because it
#   modifies service configuration
# - it only bootstraps repo-backed services automatically
# - it verifies each deployment reaches SUCCESS before continuing

# shellcheck shell=bash

set -Eeuo pipefail

readonly ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly DEPLOY_TIMEOUT_SECONDS=900
readonly DEPLOY_POLL_INTERVAL_SECONDS=10
readonly CREATE_MISSING_SERVICES="${INPUT_CREATE_MISSING_SERVICES:-no}"
readonly BACKEND_ALGORITHM="${BACKEND_ALGORITHM:-HS256}"
readonly CHROMA_COLLECTION_NAME="${CHROMA_COLLECTION_NAME:-rag_documents}"
readonly MOCK_PROVIDER_RESPONSES_LOWER="${MOCK_PROVIDER_RESPONSES:-false}"
readonly RAILWAY_POSTGRES_SERVICE="${RAILWAY_POSTGRES_SERVICE:-}"

declare -a CREATED_SERVICES=()

cd "${ROOT_DIR}"

cleanup() {
  rm -rf "${ROOT_DIR}/.railway"
}

on_error() {
  local exit_code="$1"
  local line_number="$2"

  printf '::error::Railway deployment failed at line %s (exit %s).\n' \
    "${line_number}" "${exit_code}" >&2
}

trap cleanup EXIT
trap 'on_error "$?" "${LINENO}"' ERR

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
    printf '%s\n' "$*" >> "${GITHUB_STEP_SUMMARY}"
  fi
}

require_command() {
  local command_name="$1"

  if ! command -v "${command_name}" >/dev/null 2>&1; then
    fail "Missing required command: ${command_name}"
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
  require_command "jq"
  require_command "railway"

  require_value "RAILWAY_API_TOKEN"
  require_value "RAILWAY_PROJECT"
  require_value "RAILWAY_ENVIRONMENT"
  require_value "RAILWAY_BACKEND_SERVICE"
  require_value "RAILWAY_FRONTEND_SERVICE"
  require_value "RAILWAY_CHROMA_SERVICE"
  require_value "RAILWAY_POSTGRES_SERVICE"
  require_value "BACKEND_SECRET_KEY"

  if [[ "${MOCK_PROVIDER_RESPONSES_LOWER,,}" != "true" ]] \
    && [[ -z "${GROQ_API_KEY:-}" ]] \
    && [[ -z "${GEMINI_API_KEY:-}" ]] \
    && [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
    fail "Set at least one of GROQ_API_KEY, GEMINI_API_KEY, or DEEPSEEK_API_KEY, or set MOCK_PROVIDER_RESPONSES=true."
  fi
}

reference_var() {
  local namespace="$1"
  local key="$2"

  printf '${{%s.%s}}' "${namespace}" "${key}"
}

https_reference_var() {
  local namespace="$1"
  local key="$2"

  printf 'https://${{%s.%s}}' "${namespace}" "${key}"
}

railway_link_project() {
  railway link \
    --project "${RAILWAY_PROJECT}" \
    --environment "${RAILWAY_ENVIRONMENT}" \
    --json >/dev/null
}

service_exists() {
  local service="$1"

  railway service status \
    --service "${service}" \
    --environment "${RAILWAY_ENVIRONMENT}" \
    --json >/dev/null 2>&1
}

mark_service_created() {
  local service="$1"

  CREATED_SERVICES+=("${service}")
}

service_was_created() {
  local service="$1"
  local created_service

  for created_service in "${CREATED_SERVICES[@]}"; do
    if [[ "${created_service}" == "${service}" ]]; then
      return 0
    fi
  done

  return 1
}

create_empty_service() {
  local service="$1"

  notice "Creating missing Railway service: ${service}"
  railway add --service "${service}" --json --yes >/dev/null
  mark_service_created "${service}"
  railway_link_project
}

attach_chroma_volume() {
  notice "Attaching a persistent Railway volume to Chroma at /data."
  railway volume add \
    --service "${RAILWAY_CHROMA_SERVICE}" \
    --environment "${RAILWAY_ENVIRONMENT}" \
    --mount-path /data \
    --json --yes >/dev/null
}

create_service_if_allowed() {
  local service="$1"

  if service_exists "${service}"; then
    notice "Using existing Railway service: ${service}"
    return
  fi

  if [[ "${CREATE_MISSING_SERVICES}" != "yes" ]]; then
    fail "Railway service '${service}' does not exist. Re-run this workflow with create_missing_services=yes to bootstrap it."
  fi

  create_empty_service "${service}"
}

ensure_backend_public_domain() {
  if [[ -n "${FRONTEND_VITE_API_URL:-}" ]]; then
    notice "Skipping backend public domain management because FRONTEND_VITE_API_URL was provided explicitly."
    return
  fi

  if ! service_was_created "${RAILWAY_BACKEND_SERVICE}"; then
    notice "Assuming backend public domain already exists for ${RAILWAY_BACKEND_SERVICE}."
    return
  fi

  notice "Creating a Railway-provided backend domain for ${RAILWAY_BACKEND_SERVICE}."
  railway domain \
    --service "${RAILWAY_BACKEND_SERVICE}" \
    --port "8000" \
    --json --yes >/dev/null
}

set_service_variables() {
  local service="$1"
  shift

  railway variable set \
    --service "${service}" \
    --environment "${RAILWAY_ENVIRONMENT}" \
    --skip-deploys \
    "$@" >/dev/null
}

configure_chroma() {
  set_service_variables \
    "${RAILWAY_CHROMA_SERVICE}" \
    "PORT=8000"
}

configure_backend() {
  local chroma_host
  local database_url

  chroma_host="$(reference_var "${RAILWAY_CHROMA_SERVICE}" "RAILWAY_PRIVATE_DOMAIN")"
  database_url="$(reference_var "${RAILWAY_POSTGRES_SERVICE}" "DATABASE_URL")"

  set_service_variables \
    "${RAILWAY_BACKEND_SERVICE}" \
    "PORT=8000" \
    "DATABASE_URL=${database_url}" \
    "SECRET_KEY=${BACKEND_SECRET_KEY}" \
    "ALGORITHM=${BACKEND_ALGORITHM}" \
    "ENVIRONMENT=production" \
    "MOCK_PROVIDER_RESPONSES=${MOCK_PROVIDER_RESPONSES_LOWER,,}" \
    "GROQ_API_KEY=${GROQ_API_KEY:-}" \
    "GEMINI_API_KEY=${GEMINI_API_KEY:-}" \
    "DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}" \
    "CHROMA_HOST=${chroma_host}" \
    "CHROMA_PORT=8000" \
    "CHROMA_SSL=false" \
    "CHROMA_COLLECTION_NAME=${CHROMA_COLLECTION_NAME}"
}

configure_frontend() {
  local api_url

  if [[ -n "${FRONTEND_VITE_API_URL:-}" ]]; then
    api_url="${FRONTEND_VITE_API_URL}"
  else
    api_url="$(https_reference_var "${RAILWAY_BACKEND_SERVICE}" "RAILWAY_PUBLIC_DOMAIN")"
  fi

  set_service_variables \
    "${RAILWAY_FRONTEND_SERVICE}" \
    "PORT=80" \
    "VITE_API_URL=${api_url}"
}

latest_deployment_json() {
  local service="$1"

  railway deployment list \
    --service "${service}" \
    --environment "${RAILWAY_ENVIRONMENT}" \
    --limit 1 \
    --json
}

latest_deployment_field() {
  local service="$1"
  local field="$2"
  local deployment_json

  deployment_json="$(latest_deployment_json "${service}")"

  jq -r --arg field "${field}" '
    def first_item:
      if type == "array" then .[0]
      elif type == "object" and (.deployments? | type == "array") then .deployments[0]
      elif type == "object" then .
      else empty
      end;
    first_item | .[$field] // empty
  ' <<< "${deployment_json}"
}

print_recent_service_logs() {
  local service="$1"

  warn "Showing the latest deployment logs for ${service}."
  railway service logs \
    --service "${service}" \
    --environment "${RAILWAY_ENVIRONMENT}" \
    --deployment \
    --latest \
    --lines 200 || true
}

wait_for_new_successful_deployment() {
  local service="$1"
  local previous_id="$2"
  local start_time
  local current_id
  local current_status

  start_time="$(date +%s)"

  while true; do
    current_id="$(latest_deployment_field "${service}" "id")"
    current_status="$(latest_deployment_field "${service}" "status")"

    if [[ -n "${current_id}" && "${current_id}" != "${previous_id}" ]]; then
      case "${current_status}" in
        SUCCESS)
          notice "Railway deployment for ${service} completed successfully."
          return
          ;;
        FAILED|CRASHED|REMOVED)
          print_recent_service_logs "${service}"
          fail "Railway deployment for ${service} finished with status ${current_status}."
          ;;
      esac
    fi

    if (( "$(date +%s)" - start_time >= DEPLOY_TIMEOUT_SECONDS )); then
      print_recent_service_logs "${service}"
      fail "Timed out waiting for a successful deployment for ${service}."
    fi

    sleep "${DEPLOY_POLL_INTERVAL_SECONDS}"
  done
}

deploy_path() {
  local service="$1"
  local path="$2"
  local previous_deployment_id

  previous_deployment_id="$(latest_deployment_field "${service}" "id")"

  log "Deploying ${service} from ${path}"
  railway up "${path}" \
    --path-as-root \
    --project "${RAILWAY_PROJECT}" \
    --environment "${RAILWAY_ENVIRONMENT}" \
    --service "${service}" \
    --verbose

  wait_for_new_successful_deployment "${service}" "${previous_deployment_id}"
}

write_summary() {
  add_summary "## Railway deploy"
  add_summary ""
  add_summary "- Branch: \`main\`"
  add_summary "- Bootstrap repo-backed services: \`${CREATE_MISSING_SERVICES}\`"
  add_summary "- Deploy order: \`chroma -> backend -> frontend\`"

  if [[ ${#CREATED_SERVICES[@]} -gt 0 ]]; then
    add_summary "- Services created on this run: \`${CREATED_SERVICES[*]}\`"
  else
    add_summary "- Services created on this run: none"
  fi

  add_summary ""
  add_summary "Safety note: this workflow does not auto-create managed Postgres anymore. Create that service intentionally first, then point \`RAILWAY_POSTGRES_SERVICE\` at its exact Railway service name."
  add_summary "Frontend note: if \`FRONTEND_VITE_API_URL\` is not set, the frontend build uses the backend service's Railway public domain reference."
}

main() {
  require_main_branch
  validate_inputs
  railway_link_project

  if ! service_exists "${RAILWAY_POSTGRES_SERVICE}"; then
    fail "Managed Railway Postgres service '${RAILWAY_POSTGRES_SERVICE}' does not exist. Create it first, then rerun this workflow."
  fi

  create_service_if_allowed "${RAILWAY_CHROMA_SERVICE}"
  create_service_if_allowed "${RAILWAY_BACKEND_SERVICE}"
  create_service_if_allowed "${RAILWAY_FRONTEND_SERVICE}"

  if service_was_created "${RAILWAY_CHROMA_SERVICE}"; then
    attach_chroma_volume
  fi

  configure_chroma
  deploy_path "${RAILWAY_CHROMA_SERVICE}" "chroma"

  configure_backend
  deploy_path "${RAILWAY_BACKEND_SERVICE}" "backend"

  ensure_backend_public_domain

  configure_frontend
  deploy_path "${RAILWAY_FRONTEND_SERVICE}" "frontend"

  write_summary
}

main "$@"
