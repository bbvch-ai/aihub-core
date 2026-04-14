# Explicit DocumentDB Catalog Backup via COPY Protocol

## Context

FerretDB's PostgreSQL backend uses the [DocumentDB extension](https://github.com/documentdb/documentdb), which owns
catalog tables (`documentdb_api_catalog.collections`, `collection_indexes`) mapping MongoDB collection names to
underlying PostgreSQL tables. `pg_dump` silently skips extension-owned table data, and DocumentDB never calls
`pg_extension_config_dump()` to opt in. We cannot patch this externally. Without a workaround, a restore has all
document data but an empty catalog — FerretDB reports zero collections.

## Decision Drivers

- **Sequence preservation**\
  Dynamic CSV-based approach would not capture sequence values. Post-restore ID collisions on first write.
- **Format fragility**\
  CSV parsing of BSON-derived catalog data introduces failure points (embedded quotes, NULLs, special characters).
- **Native protocol reliability**\
  PostgreSQL's `COPY` protocol passes data as an opaque byte stream — no intermediate parsing.

## Decision

Hardcoded list of DocumentDB catalog tables and sequences with native `COPY TO STDOUT` / `COPY FROM stdin` protocol.
Backup produces `ext-catalog.sql.gz`; restore replays it after `pg_restore`. Restore skips gracefully when the artifact
doesn't exist (backward compatible). Discovery query in source comments for verifying completeness against new extension
versions.

## Consequences

### Positive

- Sequence values preserved, no ID collisions
- No intermediate parsing — psql handles escaping natively
- Failures raise immediately instead of producing silent incomplete backups

### Trade-offs

- Hardcoded list must be updated manually if DocumentDB adds new catalog tables (discovery query mitigates this)
