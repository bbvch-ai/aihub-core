#!/bin/bash
set -e
# Nuxt MCP — official Nuxt framework documentation server.
# Provides version-specific framework docs, API references, deployment guides,
# and blog posts. The swiss_ai_hub_web frontend is built with Nuxt 3.
#
# Uses the official remote MCP endpoint at nuxt.com.
cd "$(dirname "$0")/../.."
exec npx -y mcp-remote@latest https://nuxt.com/mcp
