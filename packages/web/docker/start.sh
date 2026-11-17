#!/bin/sh
# Renders the per-deployment runtime config and the nginx server block, then starts nginx. The Content-Security-Policy
# names the Keycloak, OpenWebUI and WebSocket origins, which are only known from the container environment. It is
# built once here because nginx repeats it in every block that sets its own headers.
set -eu

origin_of() {
  printf '%s' "${1:-}" | sed -nE 's|^([a-zA-Z][a-zA-Z0-9+.-]*://[^/?#]+).*$|\1|p'
}

KEYCLOAK_ORIGIN="$(origin_of "${OAUTH_AUTHORITY_URL:-}")"
WEBUI_ORIGIN="$(origin_of "${WEBUI_URL:-}")"
WS_ORIGIN="$(origin_of "${WS_ENDPOINT:-}")"
# Markdown images and knowledge uploads go to the S3 gateway through presigned URLs. Without a configured endpoint any
# https origin stays allowed, so a deployment that has not set it yet keeps working.
S3_ORIGIN="$(origin_of "${S3_STORAGE_PUBLIC_ENDPOINT:-}")"
S3_ORIGIN="${S3_ORIGIN:-https:}"
CSP_SCRIPT_HASHES="$(cat /etc/nginx/aihub/csp-script-hashes)"

CONTENT_SECURITY_POLICY="default-src 'self'; script-src 'self' ${CSP_SCRIPT_HASHES}; style-src 'self' 'unsafe-inline'; \
img-src 'self' data: blob: ${S3_ORIGIN}; font-src 'self' data:; \
connect-src 'self' ${KEYCLOAK_ORIGIN} ${WS_ORIGIN} ${S3_ORIGIN} https://api.iconify.design https://api.simplesvg.com https://api.unisvg.com; \
frame-src 'self' blob: ${WEBUI_ORIGIN} ${KEYCLOAK_ORIGIN}; form-action 'self' ${WEBUI_ORIGIN} ${KEYCLOAK_ORIGIN}; \
frame-ancestors 'self'; object-src 'none'; base-uri 'self'"
export CONTENT_SECURITY_POLICY

envsubst < /usr/share/nginx/html/config.template.js > /usr/share/nginx/html/config.js
envsubst '${CONTENT_SECURITY_POLICY}' < /etc/nginx/aihub/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
