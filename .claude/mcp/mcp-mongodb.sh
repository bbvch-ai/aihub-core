#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi
exec docker run --rm -i --network=host \
  -e "MDB_MCP_CONNECTION_STRING=mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@localhost:27017/aihub" \
  -e MDB_MCP_READ_ONLY=true \
  mongodb/mongodb-mcp-server:latest
