#!/bin/bash
set -e
# Dagster MCP — MCP server for Dagster data pipeline orchestration.
# Explore pipelines, monitor runs, manage assets, and inspect jobs via natural language.
# Dagster powers the aihub_pipeline data ingestion and processing workflows.
#
# Connects to the local Dagster instance. When running in Docker, the webserver
# is exposed on port 3002 (maps to internal 3000). For local dev, runs on 3000.
# Dagster does not require authentication in dev mode.
# Requires uv (pip install uv) for fast startup.
cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi

DAGSTER_URL="${DAGSTER_WEBSERVER_URL:-http://localhost:3002}"

exec uvx mcp-server-dagster --url "$DAGSTER_URL"
