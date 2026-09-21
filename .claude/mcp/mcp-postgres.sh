#!/bin/bash
set -e
# PostgreSQL MCP — read-only access to the PostgreSQL databases backing the platform
# (OpenWebUI chat, Langfuse traces, Dagster run history, LiteLLM routing, Keycloak).
#
# Uses Crystal DBA's postgres-mcp. The previous server, @modelcontextprotocol/server-postgres,
# was a reference example that is now deprecated on npm and archived upstream
# (modelcontextprotocol/servers-archived), last released 2024-12-04, and exposed a single
# `query` tool.
#
# Tools: list_schemas, list_objects, get_object_details, explain_query, execute_sql,
# analyze_db_health, plus index-tuning tools that need extensions this stack does not load
# (analyze_workload_indexes and get_top_queries require pg_stat_statements, which needs
# shared_preload_libraries; analyze_query_indexes requires hypopg, absent from the image).
#
# --access-mode=restricted keeps it read-only, matching MDB_MCP_READ_ONLY on the MongoDB server.
#
# postgres-mcp is MCP-SDK-v1 code, so `mcp` is pinned below 2.x (same as mcp-server-milvus);
# the server version is pinned so every developer runs the same build.
#
# PostgreSQL cannot query across databases, so this connects to one database at a time.
# POSTGRES_MCP_DB selects it (default: openwebui). The `postgres` database holds no
# application tables — pointing here is what makes the server able to read anything at all.
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Extract only the variables we need from .env (strip surrounding quotes).
_extract_env() { grep "^$1=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//'; }
if [[ -f "$PROJECT_ROOT/.env" ]]; then
  POSTGRES_USER=$(_extract_env POSTGRES_USER)
  POSTGRES_PASSWORD=$(_extract_env POSTGRES_PASSWORD)
  POSTGRES_HOST=$(_extract_env POSTGRES_HOST)
  POSTGRES_PORT=$(_extract_env POSTGRES_PORT)
  POSTGRES_MCP_DB=$(_extract_env POSTGRES_MCP_DB)
fi

PGUSER="${POSTGRES_USER:-postgres}"
PGPASS="${POSTGRES_PASSWORD:-postgres}"
PGHOST="${POSTGRES_HOST:-localhost}"
PGPORT="${POSTGRES_PORT:-5432}"
PGDATABASE="${POSTGRES_MCP_DB:-openwebui}"

cd /tmp
exec uvx --from postgres-mcp==0.3.0 --with 'mcp<2' postgres-mcp \
  --access-mode=restricted \
  "postgresql://${PGUSER}:${PGPASS}@${PGHOST}:${PGPORT}/${PGDATABASE}"
