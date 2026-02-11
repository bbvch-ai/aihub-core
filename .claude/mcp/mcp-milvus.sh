#!/bin/bash
set -e
# Milvus MCP — official MCP server for the Milvus vector database (by Zilliz).
# Provides runtime interaction: manage collections, run vector searches, inspect indexes,
# and query embeddings. Milvus is the primary vector store for semantic search in the platform.
#
# Connection uses credentials from .env (MILVUS_ROOT_PASSWORD).
# Requires uv (pip install uv) for fast startup.
cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi

# .env.dev uses MILVUS_URL for the endpoint and MILVUS_ROOT_PASSWORD for auth.
# The compose constructs MILVUS_TOKEN as "root:<password>" for services running inside Docker.
MILVUS_HOST="${MILVUS_URL:-http://localhost:19530}"
MILVUS_AUTH="${MILVUS_TOKEN:-root:${MILVUS_ROOT_PASSWORD:-Milvus}}"

exec uvx mcp-server-milvus \
  --uri "$MILVUS_HOST" \
  --token "$MILVUS_AUTH"
