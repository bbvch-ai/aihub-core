#!/bin/sh
# =============================================================================
# OpenWebUI Initialization Script (PostgreSQL Direct Insert)
# =============================================================================
# Registers functions from Python files and creates the AI-Hub service account.
#
# Generated from template. Do not edit directly.
# =============================================================================

set -e

POSTGRES_HOST="${POSTGRES_HOST}"
POSTGRES_PORT="${POSTGRES_PORT}"
POSTGRES_DB="${POSTGRES_DB}"
POSTGRES_USER="${POSTGRES_USER}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
FUNCTIONS_DIR="${FUNCTIONS_DIR}"

export PGPASSWORD="$POSTGRES_PASSWORD"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

run_sql() {
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAq "$@"
}

# Wait for PostgreSQL to be ready
wait_for_postgres() {
    log "Waiting for PostgreSQL to be ready..."
    until run_sql -c '\q' 2>/dev/null; do
        log "PostgreSQL not ready, waiting 5s..."
        sleep 5
    done
    log "PostgreSQL is ready!"
}

# Extract metadata from Python file docstring
extract_metadata() {
    file="$1"
    field="$2"
    grep -m1 "^${field}:" "$file" 2>/dev/null | sed "s/^${field}:[[:space:]]*//" || echo ""
}

# Generate a deterministic ID from filename
generate_id() {
    basename "$1" .py | tr '[:upper:]' '[:lower:]' | tr '_' '-'
}

# Determine function type from file content
get_function_type() {
    if grep -q "class Pipe" "$1"; then
        echo "pipe"
    elif grep -q "class Filter" "$1"; then
        echo "filter"
    elif grep -q "class Action" "$1"; then
        echo "action"
    else
        echo "pipe"
    fi
}

# Build meta JSON from extracted metadata
build_meta_json() {
    description="$1"
    icon_url="$2"

    # Escape for JSON
    desc_escaped=$(echo "$description" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')

    if [ -n "$icon_url" ]; then
        icon_escaped=$(echo "$icon_url" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')
        echo "{\"description\": \"${desc_escaped}\", \"manifest\": {\"icon_url\": \"${icon_escaped}\"}}"
    else
        echo "{\"description\": \"${desc_escaped}\"}"
    fi
}

# Register a single function via PostgreSQL
register_function() {
    file="$1"
    func_id=$(generate_id "$file")
    title=$(extract_metadata "$file" "title")
    description=$(extract_metadata "$file" "description")
    icon_url=$(extract_metadata "$file" "icon_url")
    func_type=$(get_function_type "$file")

    # Default values if not found
    title="${title:-$func_id}"
    description="${description:-Auto-registered function}"

    # Build meta JSON
    meta_json=$(build_meta_json "$description" "$icon_url")

    # Get current timestamp
    timestamp=$(date +%s)

    log "Registering function: $func_id (type: $func_type, title: $title)"

    # Read the file content and use a temp file for the SQL
    # This avoids shell escaping issues
    tmpfile=$(mktemp)

    cat > "$tmpfile" << 'SQLHEADER'
DO $$
DECLARE
    v_content TEXT;
BEGIN
    v_content := $CONTENT$
SQLHEADER

    cat "$file" >> "$tmpfile"

    cat >> "$tmpfile" << SQLFOOTER
\$CONTENT\$;

    INSERT INTO function (id, user_id, name, type, content, meta, is_active, is_global, created_at, updated_at)
    VALUES (
        '${func_id}',
        '',
        '$(echo "$title" | sed "s/'/''/g")',
        '${func_type}',
        v_content,
        '${meta_json}'::jsonb,
        true,
        true,
        ${timestamp},
        ${timestamp}
    )
    ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        type = EXCLUDED.type,
        content = EXCLUDED.content,
        meta = EXCLUDED.meta,
        is_active = EXCLUDED.is_active,
        is_global = EXCLUDED.is_global,
        updated_at = EXCLUDED.updated_at;
END
\$\$;
SQLFOOTER

    if run_sql -f "$tmpfile" 2>&1; then
        log "Successfully registered function: $func_id"
        rm -f "$tmpfile"
        return 0
    else
        log "WARNING: Failed to register function: $func_id"
        rm -f "$tmpfile"
        return 1
    fi
}

# Create AI-Hub service account for API access (JWT-authenticated model management)
create_service_account() {
    SERVICE_ACCOUNT_ID="${OPENWEBUI_SERVICE_ACCOUNT_ID}"
    if ! echo "${SERVICE_ACCOUNT_ID}" | grep -qE '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'; then
        log "ERROR: OPENWEBUI_SERVICE_ACCOUNT_ID is not a valid UUID"
        return 1
    fi
    SERVICE_ACCOUNT_EMAIL="aihub-service@aihub.internal"
    SERVICE_ACCOUNT_NAME="AI-Hub Service Account"
    SERVICE_ACCOUNT_PASSWORD=$(openssl passwd -6 "$(openssl rand -hex 32)")
    TIMESTAMP=$(date +%s)

    log "Creating AI-Hub service account admin..."


    run_sql \
        -v svc_id="${SERVICE_ACCOUNT_ID}" \
        -v svc_name="${SERVICE_ACCOUNT_NAME}" \
        -v svc_email="${SERVICE_ACCOUNT_EMAIL}" \
        -v svc_password="${SERVICE_ACCOUNT_PASSWORD}" \
        -v svc_timestamp="${TIMESTAMP}" \
        -c "
        INSERT INTO \"user\" (id, name, email, role, profile_image_url, created_at, updated_at, last_active_at)
        VALUES (
            :'svc_id',
            :'svc_name',
            :'svc_email',
            'admin',
            '/user.png',
            :'svc_timestamp'::bigint,
            :'svc_timestamp'::bigint,
            :'svc_timestamp'::bigint
        )
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            email = EXCLUDED.email,
            role = EXCLUDED.role,
            updated_at = EXCLUDED.updated_at;

        INSERT INTO auth (id, email, password, active)
        VALUES (
            :'svc_id',
            :'svc_email',
            :'svc_password',
            true
        )
        ON CONFLICT DO NOTHING;
    " 2>&1 && log "Service account ready" || log "WARNING: Service account creation failed"
}

# Main execution
main() {
    log "Starting OpenWebUI function registration (PostgreSQL direct insert)..."

    # Wait for PostgreSQL
    wait_for_postgres

    # Wait for OpenWebUI to initialize database schema
    log "Waiting for OpenWebUI to initialize database schema..."
    sleep 10

    # Check if function table exists
    retries=0
    max_retries=6
    while [ $retries -lt $max_retries ]; do
        table_exists=$(run_sql -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'function');" 2>/dev/null || echo "f")

        if [ "$table_exists" = "t" ]; then
            break
        fi

        retries=$((retries + 1))
        log "Function table does not exist yet. Attempt $retries/$max_retries, waiting 10s..."
        sleep 10
    done

    if [ "$table_exists" != "t" ]; then
        log "ERROR: Function table does not exist after waiting. OpenWebUI may not have started properly."
        exit 1
    fi

    log "Function table exists, proceeding..."

    # Create AI-Hub service account admin for API access
    create_service_account

    # Find and register all Python files
    registered=0
    failed=0

    for file in "${FUNCTIONS_DIR}"/*.py; do
        [ -f "$file" ] || continue

        # Skip __init__.py and similar
        filename=$(basename "$file")
        case "$filename" in
            __*.py) continue ;;
        esac

        if register_function "$file"; then
            registered=$((registered + 1))
        else
            failed=$((failed + 1))
        fi
    done

    log "Function registration complete: $registered registered, $failed failed"
}

main "$@"
