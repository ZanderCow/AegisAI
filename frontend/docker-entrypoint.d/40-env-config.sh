#!/bin/sh
set -eu

escape_js_string() {
  printf '%s' "${1}" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

api_url="$(escape_js_string "${VITE_API_URL:-}")"

cat >/usr/share/nginx/html/env-config.js <<EOF
window.__APP_CONFIG__ = {
  VITE_API_URL: "${api_url}"
};
EOF
