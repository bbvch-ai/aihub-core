#!/bin/bash
set -e
# NATS MCP — proper MCP server for NATS messaging system integration.
# Provides message viewing, subject inspection, JetStream stream management,
# and monitoring. NATS is the event-driven backbone for the Swiss AI Agent Protocol.
#
# Uses the certified mcp-nats server (sinadarbouy/mcp-nats) via Docker.
# Connection uses NATS_TOKEN from .env for authentication.
cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi

# .env.dev uses NATS_ENDPOINT for the connection URL and NATS_TOKEN for auth.
NATS_HOST="${NATS_ENDPOINT:-${NATS_URL:-nats://localhost:4222}}"

docker_args=(
  run -i --rm --init
  --network=host
  -e "NATS_URL=$NATS_HOST"
)

if [[ -n "$NATS_TOKEN" ]]; then
  docker_args+=(-e "NATS_TOKEN=$NATS_TOKEN")
else
  docker_args+=(-e "NATS_NO_AUTHENTICATION=true")
fi

exec docker "${docker_args[@]}" cnadb/mcp-nats --transport stdio
