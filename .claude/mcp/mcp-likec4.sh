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
#
# Pinned to the v1 line for reproducible agent behaviour (matches the `likec4`
# CLI pin in docs/package.json). Bump deliberately when upgrading the model tooling.
#
# The workspace is the current directory (or $LIKEC4_WORKSPACE) — so we cd into
# docs/likec4, not the repo root. The server's only default exclude is
# `**/node_modules/**`, so a repo-root workspace would scan and file-watch .venv/,
# .git/ and infra/.docker-volumes/, and would miss a docs/likec4/likec4.config.json.
cd "$(dirname "$0")/../../docs/likec4"
exec npx -y "@likec4/mcp@1"
