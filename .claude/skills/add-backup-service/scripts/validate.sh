#!/usr/bin/env bash
# validate.sh — Check registration points for a backup service
# Usage: bash .claude/skills/add-backup-service/scripts/validate.sh ServiceName
#   e.g.: bash .claude/skills/add-backup-service/scripts/validate.sh PostgreSQL
set -euo pipefail

SERVICE="${1:?Usage: validate.sh <ServiceName> (e.g. PostgreSQL, Milvus, Neo4j)}"
ERRORS=0
WARNINGS=0
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

BACKUP_DIR="$ROOT/aihub_backup/aihub_backup"
COMPOSE="$ROOT/deployment/templates/docker-compose.yml.j2"
ENV_DEV="$ROOT/.env.dev"
ENV_PROD="$ROOT/.env.prod"

echo "=== Validating backup registration: $SERVICE ==="
echo ""

# --- Step 1: Handler file exists ---
HANDLER_LOWER=$(echo "$SERVICE" | tr '[:upper:]' '[:lower:]' | tr -d ' ')

HANDLER_FILE=$(find "$BACKUP_DIR/services/" -name "*.py" -not -name "base.py" -not -name "__init__.py" \
  -exec grep -l "\"$SERVICE\"" {} \; 2>/dev/null | head -1)

if [ -n "$HANDLER_FILE" ]; then
  echo "PASS [1] Handler file: $(basename "$HANDLER_FILE")"
elif [ -f "$BACKUP_DIR/services/${HANDLER_LOWER}.py" ]; then
  echo "PASS [1] Handler file: ${HANDLER_LOWER}.py"
else
  echo "FAIL [1] No handler file found for '$SERVICE' in $BACKUP_DIR/services/"
  ERRORS=$((ERRORS + 1))
fi

# --- Step 2: BACKUP_SERVICES + SERVICE_TO_ASSET_KEY ---
if grep -q "\"$SERVICE\"" "$BACKUP_DIR/models.py" 2>/dev/null; then
  IN_TUPLE=$(grep -c "\"$SERVICE\"" "$BACKUP_DIR/models.py" 2>/dev/null || echo 0)
  if [ "$IN_TUPLE" -ge 2 ]; then
    echo "PASS [2] models.py: BACKUP_SERVICES + SERVICE_TO_ASSET_KEY"
  else
    echo "WARN [2] models.py: '$SERVICE' found $IN_TUPLE time(s), expected in both BACKUP_SERVICES and SERVICE_TO_ASSET_KEY"
    WARNINGS=$((WARNINGS + 1))
  fi
else
  echo "FAIL [2] '$SERVICE' not found in $BACKUP_DIR/models.py"
  ERRORS=$((ERRORS + 1))
fi

# --- Step 3: HANDLER_FACTORIES in handler_factory.py ---
if grep -q "\"$SERVICE\"" "$BACKUP_DIR/dagster/assets/handler_factory.py" 2>/dev/null; then
  echo "PASS [3] handler_factory.py: HANDLER_FACTORIES entry"
else
  echo "FAIL [3] '$SERVICE' not found in $BACKUP_DIR/dagster/assets/handler_factory.py"
  ERRORS=$((ERRORS + 1))
fi

# --- Step 4: Asset key in definitions.py ---
if grep -q "\"$SERVICE\"" "$BACKUP_DIR/dagster/definitions.py" 2>/dev/null; then
  echo "PASS [4] definitions.py: Asset key for '$SERVICE'"
else
  echo "FAIL [4] '$SERVICE' not found in $BACKUP_DIR/dagster/definitions.py"
  ERRORS=$((ERRORS + 1))
fi

# --- Step 5: SERVICE_DEPS entry ---
if grep -q "\"$SERVICE\"" "$BACKUP_DIR/container_lifecycle.py" 2>/dev/null; then
  echo "PASS [5] container_lifecycle.py: SERVICE_DEPS entry"
else
  echo "FAIL [5] '$SERVICE' not found in $BACKUP_DIR/container_lifecycle.py"
  ERRORS=$((ERRORS + 1))
fi

# --- Step 6: Validation check in restore_session_factory.py ---
if grep -q "_validate_backup_completeness_or_raise" "$BACKUP_DIR/dagster/assets/restore_session_factory.py" 2>/dev/null; then
  echo "PASS [6] restore_session_factory.py: _validate_backup_completeness_or_raise() exists"
else
  echo "FAIL [6] _validate_backup_completeness_or_raise() not found in restore_session_factory.py"
  ERRORS=$((ERRORS + 1))
fi

# --- Step 7: Settings fields ---
if grep -qi "${HANDLER_LOWER}\|${SERVICE}" "$BACKUP_DIR/settings.py" 2>/dev/null; then
  echo "PASS [7] settings.py: Credential fields present"
else
  echo "WARN [7] No obvious '$SERVICE' fields in settings.py — verify manually"
  WARNINGS=$((WARNINGS + 1))
fi

# --- Step 8: Compose env vars ---
if [ -f "$COMPOSE" ]; then
  BACKUP_BLOCK=$(awk '/container_name: backup/,/^  [a-z]/' "$COMPOSE" 2>/dev/null)
  if echo "$BACKUP_BLOCK" | grep -qi "${HANDLER_LOWER}\|${SERVICE}" 2>/dev/null; then
    echo "PASS [8] docker-compose.yml.j2: Backup env vars reference '$SERVICE'"
  else
    echo "WARN [8] No '$SERVICE' references in backup service compose block — may use generic vars"
    WARNINGS=$((WARNINGS + 1))
  fi
else
  echo "SKIP [8] Compose template not found at $COMPOSE"
  WARNINGS=$((WARNINGS + 1))
fi

# --- Step 9: .env files ---
if [ -f "$ENV_DEV" ]; then
  echo "PASS [9] .env.dev exists (verify backup-specific vars manually)"
else
  echo "WARN [9] .env.dev not found"
  WARNINGS=$((WARNINGS + 1))
fi

# --- Summary ---
echo ""
echo "=== Results ==="
echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"

if [ "$ERRORS" -gt 0 ]; then
  echo "VERDICT: FAIL — $ERRORS registration point(s) missing"
  exit 1
elif [ "$WARNINGS" -gt 2 ]; then
  echo "VERDICT: NEEDS REVIEW — $WARNINGS items need manual verification"
  exit 0
else
  echo "VERDICT: PASS — all registration points verified"
  exit 0
fi
