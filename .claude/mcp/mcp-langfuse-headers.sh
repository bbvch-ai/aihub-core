#!/bin/bash
set -e
# Auth headers for the Langfuse MCP server, which Claude Code connects to over HTTP directly.
#
# Langfuse authenticates with Basic auth over base64(LANGFUSE_PUBLIC_KEY:LANGFUSE_SECRET_KEY).
# Those keys live in .env, which .mcp.json cannot read — its ${VAR} expansion resolves against
# the shell environment — so this helper bridges the two. Claude Code runs it on every
# connection and expects a JSON object of headers on stdout.
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

_extract_env() { grep "^$1=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//'; }

PK=$(_extract_env LANGFUSE_PUBLIC_KEY)
SK=$(_extract_env LANGFUSE_SECRET_KEY)

if [[ -z "$PK" || -z "$SK" ]]; then
  echo "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set in .env" >&2
  exit 1
fi

printf '{"Authorization": "Basic %s"}\n' "$(printf '%s:%s' "$PK" "$SK" | base64 -w 0)"
