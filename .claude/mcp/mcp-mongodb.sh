#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
source .env
exec docker run --rm -i --network=host \
  -e "MDB_MCP_CONNECTION_STRING=mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@localhost:27017/aihub" \
  -e MDB_MCP_READ_ONLY=true \
  mongodb/mongodb-mcp-server:latest
