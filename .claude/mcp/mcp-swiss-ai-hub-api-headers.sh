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

_extract_env() { grep "^$1=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//'; }

TOKEN=$(_extract_env SUPERUSER_TOKEN)

if [[ -z "$TOKEN" ]]; then
  echo "SUPERUSER_TOKEN must be set in .env" >&2
  exit 1
fi

printf '{"Authorization": "Bearer %s"}\n' "$TOKEN"
