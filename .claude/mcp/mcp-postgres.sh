#!/bin/bash
set -e
# PostgreSQL MCP — read-only access to the PostgreSQL databases backing the platform.
# Complements MongoDB MCP by providing lower-level access to the infrastructure databases
# used by Langfuse (traces), Dagster (pipelines), LiteLLM (routing), and OpenWebUI (chat).
#
# Tools: query (read-only SQL), list_tables, describe_table
# Connection uses credentials from .env (POSTGRES_USER, POSTGRES_PASSWORD).
cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi

PGUSER="${POSTGRES_USER:-postgres}"
PGPASS="${POSTGRES_PASSWORD:-postgres}"
PGHOST="${POSTGRES_HOST:-localhost}"
PGPORT="${POSTGRES_PORT:-5432}"

# Connect to the main postgres database (has access to all schemas)
exec npx -y @modelcontextprotocol/server-postgres \
  "postgresql://${PGUSER}:${PGPASS}@${PGHOST}:${PGPORT}/postgres"
