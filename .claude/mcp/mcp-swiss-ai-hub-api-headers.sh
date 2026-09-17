#!/bin/bash
set -e
# Auth headers for the platform's own MCP endpoint, which Claude Code connects to over HTTP
# directly. The API accepts the superuser bearer token from .env; Keycloak admin-cli tokens
# are rejected.
#
# .mcp.json cannot read .env — its ${VAR} expansion resolves against the shell environment —
# so this helper bridges the two. Claude Code runs it on every connection and expects a JSON
# object of headers on stdout.
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# This emits a superuser credential, so refuse to hand it to anything but the local API.
# Claude Code passes the resolved endpoint in CLAUDE_CODE_MCP_SERVER_URL; the URL in
# .mcp.json is hard-coded to loopback, and this guard keeps the token from leaking should
# anyone later make it configurable.
case "${CLAUDE_CODE_MCP_SERVER_URL:-}" in
  "" | http://localhost:* | http://127.0.0.1:* | "http://[::1]:"*) ;;
  *)
    echo "Refusing to send the superuser token to non-loopback endpoint: $CLAUDE_CODE_MCP_SERVER_URL" >&2
    exit 1
    ;;
esac

_extract_env() { grep "^$1=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//'; }

TOKEN=$(_extract_env SUPERUSER_TOKEN)

if [[ -z "$TOKEN" ]]; then
  echo "SUPERUSER_TOKEN must be set in .env" >&2
  exit 1
fi

printf '{"Authorization": "Bearer %s"}\n' "$TOKEN"
