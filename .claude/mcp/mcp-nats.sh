#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
# NATS monitoring API for message bus observability.
# NATS exposes monitoring endpoints at http://localhost:8222 (/connz, /routez, /subsz, /varz).
# Falls back to a hint if native MCP is not available.
exec npx -y mcp-remote@latest http://localhost:8222/mcp 2>/dev/null || \
  echo "NATS monitoring not available as MCP. Use HTTP directly: http://localhost:8222"
