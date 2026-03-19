#!/bin/bash
# SessionStart hook: Set up the development environment at the start of a Claude Code session.
# Local sessions run make use-local-core. Web sessions install dependencies from scratch.

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT" || exit 0

# Print current branch
current_branch=$(git branch --show-current 2>/dev/null)
echo "Branch: $current_branch" >&2

# Warn if on main branch
if [[ "$current_branch" == "main" || "$current_branch" == "master" ]]; then
  echo "WARNING: You are on the main branch. Create a feature branch before making changes." >&2
fi

# Check Docker status (quick check)
if command -v docker &>/dev/null; then
  running=$(docker compose -f infra/docker-compose.dev.yml ps --format json 2>/dev/null | head -1)
  if [[ -z "$running" ]]; then
    echo "Docker dev stack is not running. Start with: make up-dev" >&2
  fi
fi

if [[ -z "$CLAUDE_CODE_REMOTE" ]]; then
  # Local session: sync all packages
  echo "Local session. Running uv sync --all-packages..." >&2
  uv sync --all-packages 2>&1 | tail -3 >&2

  # Install frontend dependencies
  if [[ -d "$REPO_ROOT/packages/web/swiss_ai_hub_web" && -f "$REPO_ROOT/packages/web/swiss_ai_hub_web/package.json" ]]; then
    (cd "$REPO_ROOT/packages/web/swiss_ai_hub_web" && pnpm install --frozen-lockfile 2>&1 | tail -1) >&2
  fi
else
  # Web session: install from scratch
  echo "Web session detected. Checking dependencies..." >&2

  # Copy .env if missing
  if [[ ! -f "$REPO_ROOT/.env" && -f "$REPO_ROOT/.env.dev" ]]; then
    cp "$REPO_ROOT/.env.dev" "$REPO_ROOT/.env"
    echo "Copied .env.dev to .env" >&2
  fi

  # Install uv if missing
  if ! command -v uv &>/dev/null; then
    echo "Installing uv..." >&2
    curl -LsSf https://astral.sh/uv/install.sh | sh 2>&1 | tail -1 >&2
  fi

  # Sync all packages
  uv sync --all-packages 2>&1 | tail -3 >&2

  # Install frontend dependencies
  if [[ -d "$REPO_ROOT/packages/web/swiss_ai_hub_web" && -f "$REPO_ROOT/packages/web/swiss_ai_hub_web/package.json" ]]; then
    (cd "$REPO_ROOT/packages/web/swiss_ai_hub_web" && pnpm install --frozen-lockfile 2>&1 | tail -1) >&2
  fi

  echo "Dependency installation complete." >&2
fi

exit 0
