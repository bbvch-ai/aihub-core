#!/bin/bash
# Stop hook: Check for uncommitted changes, untracked files, and unpushed commits.
# Reminds the developer to commit and push before ending a session.

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT" || exit 0

issues=()

# Check for staged but uncommitted changes
if ! git diff --cached --quiet 2>/dev/null; then
  issues+=("There are staged but uncommitted changes.")
fi

# Check for unstaged modifications
if ! git diff --quiet 2>/dev/null; then
  issues+=("There are unstaged modifications in tracked files.")
fi

# Check for untracked files (excluding common generated/temp files)
untracked=$(git ls-files --others --exclude-standard 2>/dev/null | head -20)
if [[ -n "$untracked" ]]; then
  issues+=("There are untracked files in the repository.")
fi

# Check for unpushed commits
current_branch=$(git branch --show-current 2>/dev/null)
if [[ -n "$current_branch" ]]; then
  upstream=$(git rev-parse --abbrev-ref "${current_branch}@{upstream}" 2>/dev/null)
  if [[ -n "$upstream" ]]; then
    unpushed=$(git log "${upstream}..HEAD" --oneline 2>/dev/null)
    if [[ -n "$unpushed" ]]; then
      issues+=("There are unpushed commits on branch '$current_branch'.")
    fi
  fi
fi

if [[ ${#issues[@]} -gt 0 ]]; then
  echo "Git hygiene check:" >&2
  for issue in "${issues[@]}"; do
    echo "  - $issue" >&2
  done
  echo "Please commit and push these changes to the remote branch." >&2
  exit 2
fi

exit 0
