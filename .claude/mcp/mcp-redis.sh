#!/bin/bash
set -e
# Redis MCP — official MCP server for Redis (by Redis Inc.), pointed at the platform's Valkey.
# Valkey is Redis-protocol compatible and holds the durable agent state that cannot be
# reconstructed from the NATS event history: RunContext and ThreadContext. This is the only
# way to inspect that state, so it pairs with the debug-agent skill.
#
# Tools: scan_keys, get/hgetall/json_get, lrange, xrange, info, dbsize, and the RediSearch
# vector-index tools. NOTE: this server has no read-only mode — unlike the MongoDB and
# PostgreSQL servers it also exposes destructive tools (delete, set, expire, rename, x/s/z-rem).
# To make it read-only, create a Valkey ACL user and point REDIS_MCP_URL at it instead:
#   ACL SETUSER claude on '>somepassword' '~*' +@read -@write
#
# Version is pinned so every developer runs the same server build.
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Extract only the variables we need from .env (strip surrounding quotes).
_extract_env() { grep "^$1=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//'; }
if [[ -f "$PROJECT_ROOT/.env" ]]; then
  REDIS_URL=$(_extract_env REDIS_URL)
  REDIS_TOKEN=$(_extract_env REDIS_TOKEN)
  REDIS_MCP_URL=$(_extract_env REDIS_MCP_URL)
fi

# .env spells the endpoint without credentials (redis://localhost:6379) and keeps the
# password in REDIS_TOKEN, so splice the two into the URI the server expects. Valkey runs
# with `--requirepass` and no username, hence the empty userinfo before the colon.
if [[ -z "$REDIS_MCP_URL" ]]; then
  REDIS_HOSTPORT="${REDIS_URL:-redis://localhost:6379}"
  REDIS_HOSTPORT="${REDIS_HOSTPORT#redis://}"
  REDIS_MCP_URL="redis://:${REDIS_TOKEN}@${REDIS_HOSTPORT}/0"
fi

# Run from /tmp: the server reads a .env from the current directory, which would otherwise
# pull in the whole project environment.
cd /tmp
exec uvx --from redis-mcp-server==0.5.1 redis-mcp-server --url "$REDIS_MCP_URL"
