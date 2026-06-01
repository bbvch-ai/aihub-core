#!/bin/bash
set -e
# LikeC4 MCP — official MCP server for the LikeC4 architecture DSL.
# Exposes the LikeC4 workspace (models, views, deployment, dynamic views) to AI assistants
# so they can read, validate, and reason about the architecture-as-code definitions.
#
# The architecture documentation under docs/ (and any .c4/.likec4 files in the repo)
# is authored in LikeC4. This server pairs with the likec4-dsl skill to give Claude
# accurate, project-specific context when editing diagrams or generating new views.
#
# See https://likec4.dev/tooling/ai-tools/ for the underlying tools.
cd "$(dirname "$0")/../.."
exec npx -y @likec4/mcp
