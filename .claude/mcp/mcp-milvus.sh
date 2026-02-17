#!/bin/bash
set -e
# Milvus MCP — official MCP server for the Milvus vector database (by Zilliz).
# Provides runtime interaction: manage collections, run vector searches, inspect indexes,
# and query embeddings. Milvus is the primary vector store for semantic search in the platform.
#
# Connection uses credentials from .env (MILVUS_ROOT_PASSWORD).
# Requires pipx (python -m pip install pipx) for isolated execution.
PROJECT_ROOT="$(dirname "$0")/../.."
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

# Extract only the variables we need from .env.
if [[ -f "$PROJECT_ROOT/.env" ]]; then
  MILVUS_URL=$(grep '^MILVUS_URL=' "$PROJECT_ROOT/.env" | cut -d'=' -f2-)
  MILVUS_ROOT_PASSWORD=$(grep '^MILVUS_ROOT_PASSWORD=' "$PROJECT_ROOT/.env" | cut -d'=' -f2-)
  MILVUS_TOKEN=$(grep '^MILVUS_TOKEN=' "$PROJECT_ROOT/.env" | cut -d'=' -f2-)
fi

MILVUS_HOST="${MILVUS_URL:-http://localhost:19530}"
MILVUS_AUTH="${MILVUS_TOKEN:-root:${MILVUS_ROOT_PASSWORD:-Milvus}}"

# mcp-server-milvus uses pydantic-settings with extra="forbid", so ANY unrecognized
# env var crashes it. pydantic-settings also reads .env from cwd by default.
# Run from /tmp to avoid picking up the project's .env file.
cd /tmp
exec pipx run mcp-server-milvus \
  --uri "$MILVUS_HOST" \
  --token "$MILVUS_AUTH"