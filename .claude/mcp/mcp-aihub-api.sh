#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi
exec npx -y mcp-remote@latest http://localhost:8000/mcp --header "Authorization: Bearer ${SUPERUSER_TOKEN}"
