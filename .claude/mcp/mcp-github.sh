#!/bin/bash
set -e
# GitHub MCP — direct access to issues, PRs, code search, CI/CD status, and project boards.
# Enables searching issues, reading PR reviews, checking workflow runs, and managing
# the aihub-core repository without leaving the coding session.
#
# SETUP: Add GITHUB_PERSONAL_ACCESS_TOKEN to your .env file.
# Create a token at: https://github.com/settings/tokens
# Required scopes: repo, read:org, read:project
cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi

if [[ -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ]]; then
  echo "GitHub MCP requires GITHUB_PERSONAL_ACCESS_TOKEN in .env" >&2
  echo "Create a token at: https://github.com/settings/tokens" >&2
  exit 1
fi

exec docker run -i --rm \
  -e "GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN" \
  ghcr.io/github/github-mcp-server
