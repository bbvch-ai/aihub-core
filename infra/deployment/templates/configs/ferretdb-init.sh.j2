#!/bin/sh
# =============================================================================
# FerretDB PostgreSQL Initialization Script
# =============================================================================
# Creates the read-only login role the knowledge content search uses to query
# its trigram indexes (KnowledgeTextIndex in packages/core). The role may read
# DocumentDB's collection catalog; the backup's ferretdb_text_index_job grants
# it SELECT on each knowledge text table it indexes, and nothing else. It also
# needs USAGE on documentdb_api_internal, where DocumentDB's planner hooks look
# up functions by name whenever a table carries a DocumentDB index; that schema
# has no SECURITY DEFINER functions, so it grants no access to data.
# Idempotent: runs on every deploy and resets the password from the env file.
#
# Generated from template. Do not edit directly.
# =============================================================================

set -e

POSTGRES_HOST="${POSTGRES_HOST}"
POSTGRES_PORT="${POSTGRES_PORT}"
POSTGRES_USER="${POSTGRES_USER}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
TEXT_SEARCH_ROLE="aihub_text_search"
TEXT_SEARCH_PASSWORD="${KNOWLEDGE_TEXT_INDEX_PASSWORD}"

export PGPASSWORD="$POSTGRES_PASSWORD"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

run_sql() {
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -tAq "$@"
}

wait_for_documentdb() {
    log "Waiting for PostgreSQL with DocumentDB's catalog..."
    until run_sql -c "SELECT 1 FROM documentdb_api_catalog.collections LIMIT 1" >/dev/null 2>&1; do
        log "Not ready, waiting 5s..."
        sleep 5
    done
}

main() {
    if [ -z "$TEXT_SEARCH_PASSWORD" ]; then
        log "KNOWLEDGE_TEXT_INDEX_PASSWORD is empty: the content search keeps scanning, no role is created"
        exit 0
    fi
    wait_for_documentdb
    run_sql -v role="$TEXT_SEARCH_ROLE" -v password="$TEXT_SEARCH_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN', :'role') WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'role') \gexec
SELECT format('ALTER ROLE %I WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L', :'role', :'password') \gexec
SELECT format('GRANT USAGE ON SCHEMA documentdb_data, documentdb_core, documentdb_api_catalog, documentdb_api_internal TO %I', :'role') \gexec
SELECT format('GRANT SELECT ON documentdb_api_catalog.collections TO %I', :'role') \gexec
SQL
    log "Role $TEXT_SEARCH_ROLE is ready"
}

main "$@"
