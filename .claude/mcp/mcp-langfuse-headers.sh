#!/bin/bash
set -e
# Auth headers for the Langfuse MCP server, which Claude Code connects to over HTTP directly.
#
# Langfuse authenticates with Basic auth over base64(LANGFUSE_PUBLIC_KEY:LANGFUSE_SECRET_KEY).
# Those keys live in .env, which .mcp.json cannot read — its ${VAR} expansion resolves against
# the shell environment — so this helper bridges the two. Claude Code runs it on every
# connection and expects a JSON object of headers on stdout.
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# These keys are credentials, so refuse to hand them to anything but the local Langfuse.
# Claude Code passes the resolved endpoint in CLAUDE_CODE_MCP_SERVER_URL; the URL in
# .mcp.json is hard-coded to loopback, and this guard keeps the keys from leaking should
# anyone later make it configurable.
case "${CLAUDE_CODE_MCP_SERVER_URL:-}" in
  "" | http://localhost:* | http://127.0.0.1:* | "http://[::1]:"*) ;;
  *)
    echo "Refusing to send Langfuse keys to non-loopback endpoint: $CLAUDE_CODE_MCP_SERVER_URL" >&2
    exit 1
    ;;
esac

_extract_env() { grep "^$1=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//'; }

PK=$(_extract_env LANGFUSE_PUBLIC_KEY)
SK=$(_extract_env LANGFUSE_SECRET_KEY)

if [[ -z "$PK" || -z "$SK" ]]; then
  echo "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set in .env" >&2
  exit 1
fi

printf '{"Authorization": "Basic %s"}\n' "$(printf '%s:%s' "$PK" "$SK" | base64 -w 0)"
