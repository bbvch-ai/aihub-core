#!/bin/bash
set -e
# MongoDB MCP — official server (mongodb/mongodb-mcp-server), read-only access to FerretDB:
# conversations, app data, agent and process events.
#
# Pinned by digest rather than by tag: the `2.1.1` tag is re-pushed on rebuilds (the registry
# also carries dated `2.1.1-YYYY-MM-DD` variants), so the plain version tag is not immutable.
# This digest is 2.1.1. Update deliberately with:
#   docker buildx imagetools inspect mongodb/mongodb-mcp-server:<version>
MONGODB_MCP_IMAGE="mongodb/mongodb-mcp-server@sha256:33c5128818e149c46bcee2f21466080eb257bb01e7add121cfc644c8d62dd387"

cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi
exec docker run --rm -i --network=host \
  -e "MDB_MCP_CONNECTION_STRING=mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@localhost:27017/aihub" \
  -e MDB_MCP_READ_ONLY=true \
  "$MONGODB_MCP_IMAGE"
