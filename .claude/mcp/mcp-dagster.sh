#!/bin/bash
set -e
# Dagster MCP — MCP server for Dagster data pipeline orchestration.
# Explore pipelines, monitor runs, manage assets, and inspect jobs via natural language.
# Dagster powers the aihub_pipeline data ingestion and processing workflows.
#
# Connects to the local Dagster instance. For local dev, runs on port 3002.
# Dagster does not require authentication in dev mode.
# Requires pipx (python -m pip install pipx) for isolated execution.
cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi

DAGSTER_URL="${DAGSTER_WEBSERVER_URL:-http://localhost:3002}"

# mcp-server-dagster requires Python >=3.12 and mcp<1.8 (FastMCP API change in 1.8+).
exec pipx run --python python3 --pip-args='mcp<1.8' --spec mcp-server-dagster \
  mcp-dagster --url "$DAGSTER_URL"