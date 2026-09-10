#!/usr/bin/env bash
# validate-issue.sh — Confirm a freshly-created issue follows bbvch-ai/aihub-core conventions
# Usage: bash .claude/skills/write-issue/scripts/validate-issue.sh <issue-number>
set -euo pipefail

ISSUE="${1:?Usage: validate-issue.sh <issue-number>}"
[[ "$ISSUE" =~ ^[0-9]+$ ]] || {
  echo "ERROR: issue must be a number (got: $ISSUE)" >&2
  exit 1
}
REPO="bbvch-ai/aihub-core"
PROJECT_NUMBER=37
ERRORS=0
WARNINGS=0

echo "=== Validating issue #$ISSUE ($REPO) ==="

JSON=$(gh issue view "$ISSUE" -R "$REPO" --json title,body,labels 2>/dev/null) || {
  echo "ERROR: Issue #$ISSUE not found in $REPO" >&2
  exit 1
}

TITLE=$(jq -r '.title' <<<"$JSON")
BODY=$(jq -r '.body // ""' <<<"$JSON")
LABELS=$(jq -r '[.labels[].name] | join(" ")' <<<"$JSON")

echo "Title:  $TITLE"
echo "Labels: ${LABELS:-<none>}"

# --- area:* label present ---
if ! grep -q 'area:' <<<"$LABELS"; then
  echo "ERROR: No area:* label. Add one per touched package (e.g. area:api)." >&2
  ERRORS=$((ERRORS + 1))
fi

# --- version label (advisory) ---
if ! grep -qE '(^| )(major|minor|patch)( |$)' <<<"$LABELS"; then
  echo "WARNING: No version label (major/minor/patch). The closing PR will need one." >&2
  WARNINGS=$((WARNINGS + 1))
fi

# --- body structure: require the bold heading at line start, not just the phrase ---
for SECTION in "In scope" "Out of scope" "Accepted when"; do
  if ! grep -qE "^\*\*${SECTION}\*\*" <<<"$BODY"; then
    echo "WARNING: Body missing '**$SECTION**' heading (expected for epics/stories/features)." >&2
    WARNINGS=$((WARNINGS + 1))
  fi
done

# --- checkbox acceptance criteria (checked or unchecked) ---
if ! grep -qE '^[[:space:]]*- \[[ xX]\]' <<<"$BODY"; then
  echo "WARNING: No checkbox acceptance criteria (- [ ]) found in 'Accepted when'." >&2
  WARNINGS=$((WARNINGS + 1))
fi

# --- on the AI-Scrum board with an Item Type ---
# Query the issue node directly: O(1) and immune to board growth (no item-list paging),
# and reads the Item Type single-select by its field name.
# shellcheck disable=SC2016  # $number is a GraphQL variable (bound via -F), not a shell expansion
BOARD_JSON=$(gh api graphql -F number="$ISSUE" -f query='
  query($number: Int!) {
    repository(owner: "bbvch-ai", name: "aihub-core") {
      issue(number: $number) {
        projectItems(first: 20) {
          nodes {
            project { number }
            fieldValueByName(name: "Item Type") {
              ... on ProjectV2ItemFieldSingleSelectValue { name }
            }
          }
        }
      }
    }
  }' 2>/dev/null || echo '{}')

ON_BOARD=$(jq -r --argjson pn "$PROJECT_NUMBER" \
  '[.data.repository.issue.projectItems.nodes[]? | select(.project.number == $pn)] | length' <<<"$BOARD_JSON")
ITEM_TYPE=$(jq -r --argjson pn "$PROJECT_NUMBER" \
  'first(.data.repository.issue.projectItems.nodes[]? | select(.project.number == $pn) | .fieldValueByName.name) // ""' <<<"$BOARD_JSON")

if [ "${ON_BOARD:-0}" -eq 0 ]; then
  echo "ERROR: Issue #$ISSUE is not on the AI-Scrum board (project $PROJECT_NUMBER)." >&2
  ERRORS=$((ERRORS + 1))
elif [ -z "$ITEM_TYPE" ]; then
  echo "WARNING: On the board but Item Type (Epic/Story/Task) is unset." >&2
  WARNINGS=$((WARNINGS + 1))
else
  echo "Board:  on AI-Scrum, Item Type=$ITEM_TYPE"
fi

echo ""
echo "=== Results ==="
echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"

if [ "$ERRORS" -gt 0 ]; then
  echo "VERDICT: FAIL — fix $ERRORS error(s)." >&2
  exit 1
fi
echo "VERDICT: PASS"
exit 0
