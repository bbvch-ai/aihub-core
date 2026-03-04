#!/usr/bin/env bash
# validate-skill.sh — Quick quality check for a SKILL.md file
# Usage: bash .claude/skills/create-or-audit-skill/scripts/validate-skill.sh path/to/SKILL.md
set -euo pipefail

SKILL_PATH="${1:?Usage: validate-skill.sh <path-to-SKILL.md>}"
ERRORS=0
WARNINGS=0

if [ ! -f "$SKILL_PATH" ]; then
  echo "ERROR: File not found: $SKILL_PATH" >&2
  exit 1
fi

SKILL_DIR=$(dirname "$SKILL_PATH")
SKILL_NAME=$(basename "$SKILL_DIR")

echo "=== Validating skill: $SKILL_NAME ==="
echo ""

# --- Structural Checks ---

# Check file is named exactly SKILL.md
BASENAME=$(basename "$SKILL_PATH")
if [ "$BASENAME" != "SKILL.md" ]; then
  echo "ERROR: File must be named SKILL.md (got: $BASENAME)" >&2
  ERRORS=$((ERRORS + 1))
fi

# Check folder naming (kebab-case)
if echo "$SKILL_NAME" | grep -qE '[A-Z _]'; then
  echo "ERROR: Folder name must be kebab-case (got: $SKILL_NAME)" >&2
  ERRORS=$((ERRORS + 1))
fi

# Check frontmatter delimiters exist
if ! head -1 "$SKILL_PATH" | grep -q '^---$'; then
  echo "ERROR: Missing opening frontmatter delimiter (---)" >&2
  ERRORS=$((ERRORS + 1))
fi

FRONTMATTER_END=$(awk '/^---$/{n++; if(n==2){print NR; exit}}' "$SKILL_PATH")
if [ -z "$FRONTMATTER_END" ]; then
  echo "ERROR: Missing closing frontmatter delimiter (---)" >&2
  ERRORS=$((ERRORS + 1))
fi

# --- Frontmatter Field Checks ---

# Check name field exists and matches folder
NAME_VAL=$(grep -m1 '^name:' "$SKILL_PATH" | sed 's/^name: *//' | tr -d '"'"'"'')
if [ -z "$NAME_VAL" ]; then
  echo "ERROR: Missing required 'name' field in frontmatter" >&2
  ERRORS=$((ERRORS + 1))
elif [ "$NAME_VAL" != "$SKILL_NAME" ]; then
  echo "WARNING: name field ($NAME_VAL) does not match folder name ($SKILL_NAME)" >&2
  WARNINGS=$((WARNINGS + 1))
fi

# Check description field exists
DESC_LINE=$(grep -n '^description:' "$SKILL_PATH" | head -1 | cut -d: -f1)
if [ -z "$DESC_LINE" ]; then
  echo "ERROR: Missing required 'description' field in frontmatter" >&2
  ERRORS=$((ERRORS + 1))
else
  # Extract full description (may be multi-line)
  DESC=$(awk -v start="$DESC_LINE" '
    NR==start { sub(/^description: */, ""); desc=$0; next }
    NR>start && /^  / { sub(/^  /, ""); desc=desc " " $0; next }
    NR>start { exit }
    END { print desc }
  ' "$SKILL_PATH")

  # Strip YAML fold/block indicators that awk may capture as part of the value
  DESC=$(echo "$DESC" | sed 's/^[>|][+-]\{0,1\} *//')

  DESC_LEN=${#DESC}
  if [ "$DESC_LEN" -gt 1024 ]; then
    echo "ERROR: Description exceeds 1024 characters ($DESC_LEN chars)" >&2
    ERRORS=$((ERRORS + 1))
  fi

  # Check for trigger phrases
  if ! echo "$DESC" | grep -qiE '(use when|use for|trigger|invoke)'; then
    echo "WARNING: Description may be missing trigger phrases (WHEN to use)" >&2
    WARNINGS=$((WARNINGS + 1))
  fi

  # Check for negative scope
  if ! echo "$DESC" | grep -qiE '(do not use|don.t use|not for|instead use)'; then
    echo "WARNING: Description missing negative scope (WHEN NOT to use)" >&2
    WARNINGS=$((WARNINGS + 1))
  fi

  # Check for XML angle brackets (forbidden)
  if echo "$DESC" | grep -qE '[<>]'; then
    echo "ERROR: Description contains XML angle brackets (< or >), which are forbidden" >&2
    ERRORS=$((ERRORS + 1))
  fi
fi

# Check for reserved names
if echo "$NAME_VAL" | grep -qiE '(^claude|^anthropic)'; then
  echo "ERROR: Skill name cannot start with 'claude' or 'anthropic' (reserved)" >&2
  ERRORS=$((ERRORS + 1))
fi

# --- Content Quality Checks ---

BODY_LINES=$(tail -n +${FRONTMATTER_END:-3} "$SKILL_PATH" 2>/dev/null | wc -l)
TOTAL_LINES=$(wc -l < "$SKILL_PATH")
WORD_COUNT=$(wc -w < "$SKILL_PATH")

echo "Size: $TOTAL_LINES lines, ~$WORD_COUNT words (~$(( WORD_COUNT * 13 / 10 )) tokens est.)"

if [ "$TOTAL_LINES" -gt 500 ]; then
  echo "WARNING: Skill exceeds 500 lines ($TOTAL_LINES). Consider moving details to references/" >&2
  WARNINGS=$((WARNINGS + 1))
fi

# Count codebase-specific references (file paths, commands)
PATH_REFS=$(grep -cE '(`[a-zA-Z_./]+/[a-zA-Z_.]+`|aihub_[a-z_]+/|apps/|packages/|src/|scripts/)' "$SKILL_PATH" 2>/dev/null || echo 0)
echo "Codebase-specific path references: $PATH_REFS"

if [ "$PATH_REFS" -lt 3 ]; then
  echo "WARNING: Fewer than 3 codebase-specific references. May be too generic." >&2
  WARNINGS=$((WARNINGS + 1))
fi

# Check for verification step
if ! grep -qiE '(verif|check|test|validate|confirm)' "$SKILL_PATH"; then
  echo "WARNING: No verification step found. Skills should end with a concrete check." >&2
  WARNINGS=$((WARNINGS + 1))
fi

# Check for common generic phrases (signals the skill may not be codebase-specific)
GENERIC_COUNT=$(grep -ciE '(best practice|clean code|solid principle|meaningful name|descriptive variable|proper error handling|well-structured|maintainable|readable code)' "$SKILL_PATH" 2>/dev/null || echo 0)
if [ "$GENERIC_COUNT" -gt 2 ]; then
  echo "WARNING: Found $GENERIC_COUNT generic programming phrases. Skill may not be codebase-specific enough." >&2
  WARNINGS=$((WARNINGS + 1))
fi

# Check that no README.md exists in the skill directory
if [ -f "$SKILL_DIR/README.md" ]; then
  echo "WARNING: README.md found in skill directory. Docs should be in SKILL.md or references/" >&2
  WARNINGS=$((WARNINGS + 1))
fi

# --- Summary ---

echo ""
echo "=== Results ==="
echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"

if [ "$ERRORS" -gt 0 ]; then
  echo "VERDICT: FAIL — fix $ERRORS error(s) before submitting" >&2
  exit 1
elif [ "$WARNINGS" -gt 3 ]; then
  echo "VERDICT: NEEDS REVISION — address warnings to improve quality" >&2
  exit 0
else
  echo "VERDICT: PASS"
  exit 0
fi