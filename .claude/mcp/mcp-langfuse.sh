#!/bin/bash
set -e
# Langfuse MCP — LLM observability: prompt management, tracing, cost tracking, evaluations.
# Native MCP server built into Langfuse at /api/public/mcp (streamableHttp).
# Auth uses Basic Auth with base64(LANGFUSE_PUBLIC_KEY:LANGFUSE_SECRET_KEY).
#
# Tools: getPrompt, listPrompts, createTextPrompt, createChatPrompt, updatePromptLabels
cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi

LANGFUSE_URL="${LANGFUSE_BASE_URL:-http://localhost:6006}"
PK="${LANGFUSE_PUBLIC_KEY:?LANGFUSE_PUBLIC_KEY must be set in .env}"
SK="${LANGFUSE_SECRET_KEY:?LANGFUSE_SECRET_KEY must be set in .env}"

AUTH_TOKEN=$(echo -n "${PK}:${SK}" | base64 -w 0)

exec npx -y mcp-remote@latest "${LANGFUSE_URL}/api/public/mcp" \
  --header "Authorization: Basic ${AUTH_TOKEN}"
