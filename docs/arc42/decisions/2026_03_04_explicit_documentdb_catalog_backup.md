# Explicit DocumentDB Catalog Backup via COPY Protocol

## Context

FerretDB's PostgreSQL backend uses the [DocumentDB extension](https://github.com/documentdb/documentdb), which owns
catalog tables (`documentdb_api_catalog.collections`, `collection_indexes`) mapping MongoDB collection names to
underlying PostgreSQL tables. `pg_dump` silently skips extension-owned table data, and DocumentDB never calls
`pg_extension_config_dump()` to opt in. We cannot patch this externally. Without a workaround, a restore has all
document data but an empty catalog — FerretDB reports zero collections.

## Decision Drivers

- **Sequence preservation**\
  Sequence values must survive backup/restore to prevent post-restore ID collisions.
- **Native protocol reliability**\
  PostgreSQL's `COPY` protocol passes data as an opaque byte stream — no intermediate parsing needed.
- **Fail-fast behavior**\
  Errors during catalog backup must be surfaced immediately, not silently produce incomplete backups.

## Decision

Hardcoded list of DocumentDB catalog tables and sequences backed up via native `COPY TO STDOUT` / `COPY FROM stdin`.
Backup produces `ext-catalog.sql.gz`; restore replays it after `pg_restore`.

## Consequences

### Positive

- Sequence values preserved, no ID collisions
- No intermediate parsing — psql handles escaping natively
- Failures raise immediately

### Trade-offs

- Hardcoded list must be updated manually if DocumentDB adds new catalog tables
