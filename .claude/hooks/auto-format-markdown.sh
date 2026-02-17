#!/bin/bash
# PostToolUse hook: Auto-format Markdown files after Edit/Write operations.
# Runs mdformat with --number on the edited file.

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Only process Edit and Write tool calls
if [[ "$tool_name" != "Edit" && "$tool_name" != "Write" ]]; then
  exit 0
fi

# Only process Markdown files
if [[ "$file_path" != *.md ]]; then
  exit 0
fi

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT" 2>/dev/null || exit 0

poetry run mdformat --number "$file_path" 2>/dev/null

# Always exit 0 — formatting is best-effort, should never block Claude
exit 0
