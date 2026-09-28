#!/bin/bash
set -e
# Dagster MCP — explore pipelines, monitor runs, inspect assets, read run logs, and manage
# schedules/sensors/backfills over the Dagster GraphQL API.
# Dagster powers the packages/pipeline data ingestion and processing workflows.
#
# Uses dagster-mcp (fabdendev/dagster-mcp). The previous server, mcp-server-dagster, was last
# released 2025-04-09 and pinned to mcp<1.8 because the FastMCP API had moved on; it exposed
# 9 tools and no access to run logs. dagster-mcp is on the current SDK (FastMCP 4.x), so no
# mcp pin is needed here.
#
# Connects to the local Dagster webserver, which for dev is started outside Docker with
# `make -C packages/pipeline document-ingestion-pipeline` (or `make playground`) on port 3000.
# OSS Dagster needs no authentication; DAGSTER_API_TOKEN applies to Dagster Cloud only.
#
# dagster-mcp is read-only by default: 17 inspection tools. Set DAGSTER_READ_ONLY=false in
# .env to also expose the 10 mutating ones (launch_job, materialize_assets, terminate_run,
# schedule/sensor toggles, backfills) — the server this replaces allowed those unconditionally.
# The safe default is kept deliberately, matching MDB_MCP_READ_ONLY on the MongoDB server and
# --access-mode=restricted on PostgreSQL: materializing a dev asset writes to NATS and Milvus
# for real.
#
# Version is pinned so every developer runs the same server build.
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Extract only the variables we need from .env (strip surrounding quotes).
_extract_env() { grep "^$1=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//'; }
if [[ -f "$PROJECT_ROOT/.env" ]]; then
  DAGSTER_WEBSERVER_URL=$(_extract_env DAGSTER_WEBSERVER_URL)
  DAGSTER_READ_ONLY=$(_extract_env DAGSTER_READ_ONLY)
fi

export DAGSTER_URL="${DAGSTER_WEBSERVER_URL:-http://localhost:3000}"
if [[ -n "$DAGSTER_READ_ONLY" ]]; then
  export DAGSTER_READ_ONLY
fi

# Run from /tmp so the server does not pick up the project's .env or a dagster.yaml from the
# repo, which would point it at a different instance than the webserver it is querying.
cd /tmp
exec uvx --from dagster-mcp==0.12.0 dagster-mcp
