#!/bin/bash
# Stop hook: Detect modified scopes and run make pr-ready on them before ending a session.
# Also warns about untracked files that may need to be staged.

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT" || exit 0

SCOPES=("aihub_lib" "aihub_agent" "aihub_process" "aihub_api" "aihub_bot" "aihub_pipeline" "aihub_web")

# Find scopes with modified files
changed_files=$(git diff --name-only 2>/dev/null)
cached_files=$(git diff --cached --name-only 2>/dev/null)
all_changed=$(echo -e "${changed_files}\n${cached_files}" | sort -u)

dirty_scopes=()
for scope in "${SCOPES[@]}"; do
  if echo "$all_changed" | grep -q "^${scope}/"; then
    dirty_scopes+=("$scope")
  fi
done

# Check for markdown changes (handled by root make format-md)
md_changed=false
if echo "$all_changed" | grep -qE '\.md$'; then
  md_changed=true
fi

# Run make pr-ready on each dirty scope
if [[ ${#dirty_scopes[@]} -gt 0 || "$md_changed" == "true" ]]; then
  echo "Running pr-ready on modified scopes before stopping..." >&2
  for scope in "${dirty_scopes[@]}"; do
    echo "  make pr-ready in $scope" >&2
  done
  if [[ "$md_changed" == "true" ]]; then
    echo "  make format-md (markdown files changed)" >&2
  fi
  exit 2
fi

# Stage untracked files
untracked=$(git ls-files --others --exclude-standard 2>/dev/null | head -20)
if [[ -n "$untracked" ]]; then
  echo "Untracked files detected — stage them with git add:" >&2
  echo "$untracked" | while read -r f; do echo "  - $f" >&2; done
  exit 2
fi

exit 0
