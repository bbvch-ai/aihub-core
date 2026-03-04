# Explicit DocumentDB Catalog Backup via COPY Protocol

## Context

AI-Hub's FerretDB instance runs on a PostgreSQL backend with the
[DocumentDB extension](https://github.com/documentdb/documentdb). This extension owns catalog tables
(`documentdb_api_catalog.collections`, `documentdb_api_catalog.collection_indexes`) and their sequences that map MongoDB
collection names and indexes to underlying PostgreSQL tables. The actual document data lives in `documentdb_data.*`
tables, which are regular (non-extension-owned) tables that `pg_dump` handles correctly.

PostgreSQL's `pg_dump` silently skips data for extension-owned tables, expecting `CREATE EXTENSION` to repopulate them
during restore. The standard fix is for extensions to call `pg_extension_config_dump()` to mark tables as
user-data-bearing — but PostgreSQL restricts this function to `CREATE EXTENSION` scripts. The DocumentDB extension never
calls it, and we cannot patch it externally.

Without a workaround, a backup/restore cycle restores all document data but leaves the catalog empty — FerretDB starts
up, sees no collection-to-table mappings, and reports zero collections despite the data being intact.

The initial implementation used a dynamic approach: query `pg_depend` to discover all extension-owned tables at backup
time, dump their rows as CSV via `COPY TO STDOUT WITH (FORMAT csv)`, parse the CSV in Python, and generate INSERT
statements. This ran per-database on every PostgreSQL host.

## Decision Drivers

- **Sequence preservation**\
  The dynamic approach did not capture sequence values (`collections_collection_id_seq`,
  `collection_indexes_index_id_seq`). After restore, auto-increment IDs would start from 1, colliding with existing rows
  on the next collection creation. This is a data corruption bug that only manifests after the first post-restore write.

- **Format fragility**\
  The CSV parsing path (`COPY TO STDOUT WITH FORMAT csv` → Python `csv.reader` → `_sql_literal()` → INSERT statements)
  introduced multiple failure points. DocumentDB catalog columns can contain arbitrary metadata (BSON-derived types,
  special characters) that stress CSV edge cases — embedded quotes, commas in values, NULL representation. A single
  parsing error silently produces incorrect INSERT statements.

- **Native protocol reliability**\
  PostgreSQL's `COPY` protocol (tab-delimited, `\.` terminator) is the canonical bulk data format. Using
  `COPY TO STDOUT` for backup and `COPY FROM stdin` for restore avoids all intermediate parsing — the data passes
  through as an opaque byte stream. psql handles escaping, NULLs, and special characters natively.

- **Scope precision**\
  The dynamic approach ran against every database on every PostgreSQL host, querying `pg_depend` even on databases that
  have no DocumentDB extension (openwebui, langfuse, dagster, litellm). This was wasteful and produced empty results for
  all non-FerretDB databases. The DocumentDB catalog exists only in the `postgres` database on the FerretDB host.

- **Error visibility**\
  The dynamic approach silently returned empty results on failure (e.g., if `pg_depend` query failed or COPY returned an
  error). A backup could complete "successfully" with missing catalog data, only discovered during a restore attempt.

## Decision

Replace dynamic extension table discovery with an explicit, hardcoded list of DocumentDB catalog tables and sequences,
and use PostgreSQL's native COPY protocol instead of CSV-to-INSERT conversion.

**Backup**: `_dump_documentdb_catalog()` runs once against the `postgres` database on the FerretDB PostgreSQL host. For
each table in `_DOCUMENTDB_CATALOG_TABLES`, it executes `COPY {table} TO STDOUT` via psql and wraps the output in
`TRUNCATE CASCADE` + `COPY FROM stdin` SQL blocks. For each sequence in `_DOCUMENTDB_CATALOG_SEQUENCES`, it reads
`last_value` and `is_called` and generates a `SELECT setval()` statement. The combined SQL is gzipped and uploaded as
`ext-catalog.sql.gz`.

**Restore**: `_restore_documentdb_catalog()` downloads and pipes the SQL through psql after `pg_restore` completes. It
checks `s3.file_exists()` first, so backups created before this change (which lack `ext-catalog.sql.gz`) are handled
gracefully.

**Maintenance**: The table and sequence lists are constants with an inline comment containing the exact SQL query to run
against a live instance to discover if new extension objects need adding:

```sql
SELECT c.relname, c.relkind FROM pg_class c
JOIN pg_depend d ON c.oid = d.objid
JOIN pg_extension e ON d.refobjid = e.oid
WHERE e.extname = 'documentdb' AND c.relkind IN ('r', 'S')
```

## Consequences

### Positive

- Sequence values are preserved across backup/restore cycles, preventing ID collisions on post-restore writes
- No intermediate parsing — data flows through psql's native COPY protocol without Python touching the content
- Failures raise `RuntimeError` immediately instead of silently producing incomplete backups
- Reduced code complexity: removed `csv`/`io` imports, `_parse_csv_row`, `_sql_literal`, `_list_extension_owned_tables`,
  `_generate_insert_statements` (net ~10 lines fewer)
- Single artifact per host (`ext-catalog.sql.gz`) instead of per-database artifacts
- Backward compatible — restore skips catalog replay when the artifact doesn't exist in S3

### Trade-offs

- If the DocumentDB extension adds new catalog tables or sequences in a future version, the hardcoded list must be
  updated manually. The discovery query in the source comment mitigates this — operators or developers can verify
  completeness against a live instance.
- `TRUNCATE CASCADE` during restore is destructive if run against a live system. This is acceptable because the entire
  restore workflow assumes all managed containers are stopped by the orchestration layer before any restore begins.
