#!/bin/bash
# PreToolUse hook: Warn about cross-scope import violations.
# Checks if a file edit introduces direct imports between scopes that bypass swiss_ai_hub.core.
# Warns but does not block (exit 0 always).

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
new_string=$(echo "$input" | jq -r '.tool_input.new_string // .tool_input.content // empty')

# Only process Edit and Write tool calls on Python files
if [[ "$tool_name" != "Edit" && "$tool_name" != "Write" ]]; then
  exit 0
fi
if [[ "$file_path" != *.py ]]; then
  exit 0
fi

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
relative_path="${file_path#$REPO_ROOT/}"
source_scope=$(echo "$relative_path" | cut -d'/' -f1-2)

# Define allowed imports per scope (everything can import swiss_ai_hub.core)
# swiss_ai_hub.process is allowed to import swiss_ai_hub.agent (documented dependency)
check_violation() {
  local import_scope="$1"

  # Same scope is always fine
  [[ "$import_scope" == "$source_scope" ]] && return 0

  # swiss_ai_hub.core is always allowed
  [[ "$import_scope" == "swiss_ai_hub.core" ]] && return 0

  # swiss_ai_hub.process may import swiss_ai_hub.agent
  [[ "$source_scope" == "packages/process" && "$import_scope" == "swiss_ai_hub.agent" ]] && return 0

  return 1
}

# Check for cross-scope imports in the new content
scopes=("swiss_ai_hub.agent" "swiss_ai_hub.api" "swiss_ai_hub.bot" "swiss_ai_hub.pipeline" "swiss_ai_hub.process")
for scope in "${scopes[@]}"; do
  if echo "$new_string" | grep -qE "from ${scope}[. ]|import ${scope}"; then
    if ! check_violation "$scope"; then
      echo "WARNING: Cross-scope import detected. '$source_scope' is importing from '$scope'." >&2
      echo "Shared code should go through swiss_ai_hub.core. See CLAUDE.md for scope boundaries." >&2
    fi
  fi
done

# Always exit 0 — warn but don't block
exit 0
