#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
source .env
exec npx -y mcp-remote@latest http://localhost:8000/mcp --header "Authorization: Bearer ${SUPERUSER_TOKEN}"
