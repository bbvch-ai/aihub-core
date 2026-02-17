#!/bin/bash
set -e
# NATS MCP — proper MCP server for NATS messaging system integration.
# Provides message viewing, subject inspection, JetStream stream management,
# and monitoring. NATS is the event-driven backbone for the Swiss AI Agent Protocol.
#
# Uses the certified mcp-nats server (sinadarbouy/mcp-nats) via Docker.
# Connection uses NATS_TOKEN from .env for authentication.
#
# Auth strategy: mcp-nats supports credentials, user/password, and anonymous modes.
# Our NATS uses token auth. We embed the token in the URL (nats://token@host:port)
# and use anonymous mode, so account_name="anonymous" in all tool calls.
cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi

# .env.dev uses NATS_ENDPOINT for the connection URL and NATS_TOKEN for auth.
NATS_BASE="${NATS_ENDPOINT:-${NATS_URL:-nats://localhost:4222}}"

# Embed token in URL for auth (nats://token@host:port).
# The nats CLI authenticates via the URL's userinfo field.
if [[ -n "$NATS_TOKEN" ]]; then
  NATS_CONNECT="${NATS_BASE/nats:\/\//nats:\/\/${NATS_TOKEN}@}"
else
  NATS_CONNECT="$NATS_BASE"
fi

exec docker run -i --rm --init \
  --network=host \
  -e "NATS_URL=$NATS_CONNECT" \
  -e "NATS_NO_AUTHENTICATION=true" \
  cnadb/mcp-nats --transport stdio
