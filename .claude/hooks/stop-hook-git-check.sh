#!/bin/bash
# Stop hook: Run make pr-ready on modified scopes and stage untracked files before ending a session.

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

# Check for markdown changes
md_changed=false
if echo "$all_changed" | grep -qE '\.md$'; then
  md_changed=true
fi

# Run make pr-ready on each dirty scope
failed=false
for scope in "${dirty_scopes[@]}"; do
  echo "Running make pr-ready in $scope..." >&2
  if ! make -C "$REPO_ROOT/$scope" pr-ready 2>&1 | tail -5 >&2; then
    echo "FAILED: make pr-ready in $scope" >&2
    failed=true
  fi
done

# Run make format-md if markdown files changed
if [[ "$md_changed" == "true" ]]; then
  echo "Running make format-md..." >&2
  if ! make -C "$REPO_ROOT" format-md 2>&1 | tail -3 >&2; then
    echo "FAILED: make format-md" >&2
    failed=true
  fi
fi

if [[ "$failed" == "true" ]]; then
  echo "Some pr-ready checks failed. Please fix before stopping." >&2
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
