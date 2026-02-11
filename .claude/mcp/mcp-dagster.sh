#!/bin/bash
set -e
# Dagster MCP — MCP server for Dagster data pipeline orchestration.
# Explore pipelines, monitor runs, manage assets, and inspect jobs via natural language.
# Dagster powers the aihub_pipeline data ingestion and processing workflows.
#
# Connects to the local Dagster instance (default: http://localhost:3000).
# Requires uv (pip install uv) for fast startup.
cd "$(dirname "$0")/../.."

DAGSTER_URL="${DAGSTER_WEBSERVER_URL:-http://localhost:3000}"

exec uvx mcp-server-dagster --url "$DAGSTER_URL"
