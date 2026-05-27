#!/bin/bash
# PostToolUse hook: Auto-format frontend files after Edit/Write operations.
# Runs ESLint fix on TypeScript and Vue files within packages/web.

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Only process Edit and Write tool calls
if [[ "$tool_name" != "Edit" && "$tool_name" != "Write" ]]; then
  exit 0
fi

# Only process TypeScript and Vue files
if [[ "$file_path" != *.ts && "$file_path" != *.vue && "$file_path" != *.tsx ]]; then
  exit 0
fi

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WEB_DIR="$REPO_ROOT/packages/web"

# Only format files within packages/web
if [[ "$file_path" == *packages/web/* ]]; then
  cd "$WEB_DIR" 2>/dev/null || exit 0
  npx eslint --fix "$file_path" 2>/dev/null
fi

# Always exit 0 — formatting is best-effort
exit 0
