# swiss-ai-hub-backup

Backup, restore, and continuous Postgres maintenance for the AI-Hub data services. Runs as an independent Dagster
instance (3 containers: gRPC code server, daemon, webserver) inside the Docker Compose project.

Requires the Docker socket (`/var/run/docker.sock`) to discover and manage platform containers via the
`com.docker.compose.project` label.

Dagster UI: `http://localhost:3004`

## What this package does

- **Daily backup** (1 AM Europe/Zurich) of PostgreSQL × 2, Milvus, Neo4j, ClickHouse, Valkey, NATS to S3 (SeaweedFS).
- **Restore** from any prior backup, partition-selected through the Dagster UI.
- **Weekly Postgres cleanup** (Sundays 3 AM) — prunes verbose Python logs and transient framework-internal events from
  the `dagster` database's `event_logs` table. UI-safe by construction: `ASSET_MATERIALIZATION`, `STEP_SUCCESS`,
  `STEP_FAILURE`, the `runs` table, and the asset catalog are never touched.
- **Monthly `pg_repack`** (first Sunday 4 AM) — reclaims disk pages on the heavy Dagster tables. The platform's Postgres
  image now ships `postgresql-17-repack` and the extension is registered on first init.

All four jobs (backup, restore, cleanup, repack) carry a `postgres-mutex=true` tag. The Dagster run coordinator caps
concurrency for that tag at one, so the jobs serialise without blocking other instance traffic.

## Configuration

Backup retention is set via `BACKUP_RETENTION_DAYS` and `BACKUP_MINIMUM_KEEP`. Maintenance is configured via
`DAGSTER_DEBUG_LOG_RETENTION_DAYS` (7), `DAGSTER_INFO_LOG_RETENTION_DAYS` (60), `DAGSTER_WARNING_LOG_RETENTION_DAYS`
(60), `DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS` (30), `DAGSTER_CLEANUP_BATCH_LIMIT` (1,000,000 — per-DELETE row cap),
and `MAINTENANCE_DISABLED` (false — kill switch).

## DocumentDB Catalog Maintenance

The PostgreSQL handler hardcodes DocumentDB extension catalog tables and sequences in `_DOCUMENTDB_CATALOG_TABLES` and
`_DOCUMENTDB_CATALOG_SEQUENCES` (`services/postgres.py`). After upgrading the DocumentDB extension, verify the list is
still complete:

```sql
SELECT c.relname, c.relkind FROM pg_class c
JOIN pg_depend d ON c.oid = d.objid
JOIN pg_extension e ON d.refobjid = e.oid
WHERE e.extname = 'documentdb' AND c.relkind IN ('r', 'S')
ORDER BY c.relkind, c.relname;
```

Run this against the `postgres` database on `postgres-ferretdb`. `relkind = 'r'` = tables, `'S'` = sequences.

## License

Copyright (C) 2024-2026 bbv Software Services AG.

AGPL-3.0-or-later — see
[packages/backup/LICENSE](https://github.com/bbvch-ai/aihub-core/blob/main/packages/backup/LICENSE). For the full
per-package matrix (root, AGPL, and proprietary packages), see
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).
