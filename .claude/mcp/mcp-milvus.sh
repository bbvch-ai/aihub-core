#!/bin/bash
set -e
# Milvus MCP — official MCP server for the Milvus vector database (by Zilliz).
# Provides runtime interaction: manage collections, run vector searches, inspect indexes,
# and query embeddings. Milvus is the primary vector store for semantic search in the platform.
#
# Connection uses credentials from .env (MILVUS_ROOT_PASSWORD).
# Requires pipx (python -m pip install pipx) for isolated execution.
#
# The version is pinned so every developer runs the same build. Upstream only ever published
# 0.1.1.dev9 (2025-11-11), a dev pre-release, so the pin also stops pipx resolving something
# unexpected should a newer pre-release appear.
PROJECT_ROOT="$(dirname "$0")/../.."
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

# Extract only the variables we need from .env (strip surrounding quotes).
_extract_env() { grep "^$1=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//'; }
if [[ -f "$PROJECT_ROOT/.env" ]]; then
  MILVUS_URL=$(_extract_env MILVUS_URL)
  MILVUS_ROOT_PASSWORD=$(_extract_env MILVUS_ROOT_PASSWORD)
  MILVUS_TOKEN=$(_extract_env MILVUS_TOKEN)
fi

MILVUS_HOST="${MILVUS_URL:-http://localhost:19530}"
MILVUS_AUTH="${MILVUS_TOKEN:-root:${MILVUS_ROOT_PASSWORD:-Milvus}}"

# mcp-server-milvus uses pydantic-settings with extra="forbid", so ANY unrecognized
# env var crashes it. pydantic-settings also reads .env from cwd by default.
# Run from /tmp to avoid picking up the project's .env, and pass config via the
# env vars that pydantic-settings expects (MILVUS_URI, MILVUS_TOKEN).
# It is also MCP-SDK-v1 code: mcp 2.x renamed FastMCP and breaks the import, so pin mcp<2.
cd /tmp
export MILVUS_URI="$MILVUS_HOST"
export MILVUS_TOKEN="$MILVUS_AUTH"
exec pipx run --pip-args='mcp<2' mcp-server-milvus==0.1.1.dev9