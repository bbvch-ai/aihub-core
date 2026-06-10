#!/usr/bin/env bash
# validate-issue.sh — Confirm a freshly-created issue follows bbvch-ai/aihub-core conventions
# Usage: bash .claude/skills/write-issue/scripts/validate-issue.sh <issue-number>
set -euo pipefail

ISSUE="${1:?Usage: validate-issue.sh <issue-number>}"
REPO="bbvch-ai/aihub-core"
PROJECT_NUMBER=37
PROJECT_OWNER="bbvch-ai"
ERRORS=0
WARNINGS=0

echo "=== Validating issue #$ISSUE ($REPO) ==="

JSON=$(gh issue view "$ISSUE" -R "$REPO" --json title,body,labels 2>/dev/null) || {
  echo "ERROR: Issue #$ISSUE not found in $REPO" >&2
  exit 1
}

TITLE=$(echo "$JSON" | python3 -c 'import json,sys;print(json.load(sys.stdin)["title"])')
BODY=$(echo "$JSON" | python3 -c 'import json,sys;print(json.load(sys.stdin)["body"] or "")')
LABELS=$(echo "$JSON" | python3 -c 'import json,sys;print(" ".join(l["name"] for l in json.load(sys.stdin)["labels"]))')

echo "Title:  $TITLE"
echo "Labels: ${LABELS:-<none>}"

# --- area:* label present ---
if ! echo "$LABELS" | grep -q 'area:'; then
  echo "ERROR: No area:* label. Add one per touched package (e.g. area:api)." >&2
  ERRORS=$((ERRORS + 1))
fi

# --- version label (advisory) ---
if ! echo "$LABELS" | grep -qE '(^| )(major|minor|patch)( |$)'; then
  echo "WARNING: No version label (major/minor/patch). The closing PR will need one." >&2
  WARNINGS=$((WARNINGS + 1))
fi

# --- body structure ---
for SECTION in "In scope" "Out of scope" "Accepted when"; do
  if ! echo "$BODY" | grep -qiF "$SECTION"; then
    echo "WARNING: Body missing '**$SECTION**' section (expected for epics/stories/features)." >&2
    WARNINGS=$((WARNINGS + 1))
  fi
done

if ! echo "$BODY" | grep -qE '^\s*- \[ \]'; then
  echo "WARNING: No checkbox acceptance criteria (- [ ]) found in 'Accepted when'." >&2
  WARNINGS=$((WARNINGS + 1))
fi

# --- on the AI-Scrum board with an Item Type ---
ITEM=$(gh project item-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --format json --limit 2000 2>/dev/null \
  | python3 -c '
import json, sys
issue = int(sys.argv[1])
data = json.load(sys.stdin)
for it in data.get("items", []):
    if (it.get("content") or {}).get("number") == issue:
        item_type = next((v for k, v in it.items() if k.lower().replace(" ", "") == "itemtype"), "")
        print(item_type or "")
        sys.exit(0)
sys.exit(3)
' "$ISSUE") && ON_BOARD=1 || ON_BOARD=0

if [ "$ON_BOARD" -ne 1 ]; then
  echo "ERROR: Issue #$ISSUE is not on the AI-Scrum board (project $PROJECT_NUMBER)." >&2
  ERRORS=$((ERRORS + 1))
elif [ -z "$ITEM" ]; then
  echo "WARNING: On the board but Item Type (Epic/Story/Task) is unset." >&2
  WARNINGS=$((WARNINGS + 1))
else
  echo "Board:  on AI-Scrum, Item Type=$ITEM"
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
