#!/bin/sh
# Renders the per-deployment runtime config and the nginx server block, then starts nginx. The Content-Security-Policy
# names the Keycloak, OpenWebUI and WebSocket origins, which are only known from the container environment.
set -eu

origin_of() {
  printf '%s' "${1:-}" | sed -nE 's|^([a-zA-Z][a-zA-Z0-9+.-]*://[^/?#]+).*$|\1|p'
}

KEYCLOAK_ORIGIN="$(origin_of "${OAUTH_AUTHORITY_URL:-}")"
WEBUI_ORIGIN="$(origin_of "${WEBUI_URL:-}")"
WS_ORIGIN="$(origin_of "${WS_ENDPOINT:-}")"
CSP_SCRIPT_HASHES="$(cat /etc/nginx/aihub/csp-script-hashes)"
export KEYCLOAK_ORIGIN WEBUI_ORIGIN WS_ORIGIN CSP_SCRIPT_HASHES

envsubst < /usr/share/nginx/html/config.template.js > /usr/share/nginx/html/config.js
envsubst '${KEYCLOAK_ORIGIN} ${WEBUI_ORIGIN} ${WS_ORIGIN} ${CSP_SCRIPT_HASHES}' \
  < /etc/nginx/aihub/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
