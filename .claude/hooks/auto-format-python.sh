#!/bin/bash
# PostToolUse hook: Auto-format Python files after Edit/Write operations.
# Detects the scope from the file path and runs Ruff format + check within that scope.

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Only process Edit and Write tool calls
if [[ "$tool_name" != "Edit" && "$tool_name" != "Write" ]]; then
  exit 0
fi

# Only process Python files
if [[ "$file_path" != *.py ]]; then
  exit 0
fi

# Determine the scope from the file path
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
relative_path="${file_path#$REPO_ROOT/}"

# Extract the scope directory (first two path components for packages/*)
scope=$(echo "$relative_path" | cut -d'/' -f1-2)

# Only format files within known scopes
case "$scope" in
  packages/core|packages/agent|packages/api|packages/bot|packages/pipeline|packages/process)
    cd "$REPO_ROOT" 2>/dev/null || exit 0
    uv run ruff format "$file_path" 2>/dev/null
    uv run ruff check --fix --ignore F401 "$file_path" 2>/dev/null
    ;;
esac

# Always exit 0 — formatting is best-effort, should never block Claude
exit 0
