#!/bin/bash
# SessionStart hook: Set up the development environment at the start of a Claude Code session.
# Detects web vs local sessions and installs dependencies accordingly.

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
  running=$(docker compose -f docker-compose.dev.yml ps --format json 2>/dev/null | head -1)
  if [[ -z "$running" ]]; then
    echo "Docker dev stack is not running. Start with: make up-dev" >&2
  fi
fi

# For web sessions, install dependencies
if [[ -n "$CLAUDE_CODE_REMOTE" ]]; then
  echo "Web session detected. Checking dependencies..." >&2

  # Copy .env if missing
  if [[ ! -f "$REPO_ROOT/.env" && -f "$REPO_ROOT/.env.dev" ]]; then
    cp "$REPO_ROOT/.env.dev" "$REPO_ROOT/.env"
    echo "Copied .env.dev to .env" >&2
  fi

  # Install Poetry if missing
  if ! command -v poetry &>/dev/null; then
    echo "Installing Poetry..." >&2
    pip install poetry 2>&1 | tail -1 >&2
  fi

  # Install Python dependencies in all scopes (background, best-effort)
  for scope in aihub_pipeline aihub_lib aihub_agent aihub_process aihub_api aihub_bot; do
    if [[ -d "$REPO_ROOT/$scope" && -f "$REPO_ROOT/$scope/pyproject.toml" ]]; then
      (cd "$REPO_ROOT/$scope" && poetry install --no-interaction 2>&1 | tail -1) &
    fi
  done

  # Install frontend dependencies (background, best-effort)
  if [[ -d "$REPO_ROOT/aihub_web/aihub_web" && -f "$REPO_ROOT/aihub_web/aihub_web/package.json" ]]; then
    (cd "$REPO_ROOT/aihub_web/aihub_web" && pnpm install --frozen-lockfile 2>&1 | tail -1) &
  fi

  # Wait for all background installs (don't block session if they fail)
  wait 2>/dev/null
  echo "Dependency installation complete." >&2
fi

exit 0
