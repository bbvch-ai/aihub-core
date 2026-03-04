# aihub_backup — Centralized Backup & Restore

Automated backup and restore orchestration for all AI-Hub stateful services. Runs as 3 Dagster containers (gRPC code
server + daemon + webserver) with no dependency on `aihub_lib`.

## What gets backed up

| Service    | Method                                            | Data                                            |
| ---------- | ------------------------------------------------- | ----------------------------------------------- |
| PostgreSQL | `pg_dumpall` + `pg_dump` (+ DocumentDB catalog¹)  | OpenWebUI, Langfuse, Dagster, LiteLLM, FerretDB |
| Milvus     | `milvus-backup` (official tool)                   | Vector collections with consistent metadata     |
| Neo4j      | `neo4j-admin` via temp container                  | Agent memory graphs                             |
| ClickHouse | `BACKUP DATABASE TO Disk()` SQL command           | Langfuse traces, observations, scores           |
| Valkey     | `BGSAVE` + RDB copy (+ temp container on restore) | Cache and session state                         |
| NATS       | `nats` CLI stream backup                          | JetStream streams                               |

All backups are stored in SeaweedFS under `s3://backups/{timestamp}/`.

## Architecture

The backup service runs its own Dagster instance with SQLite storage — it does not share the PostgreSQL-backed Dagster
instance used by `aihub_pipeline`. This is intentional: because it backs up PostgreSQL, it cannot depend on PostgreSQL
for its own state.

**Backup flow**: A fan-out asset graph stops all managed containers, runs per-service backups in parallel, then restarts
everything. Individual service failures do not block other backups — the run fails at finalize if any service failed.

**Restore flow**: Validates backup completeness, stops all managed containers, restores each service in parallel, then
restarts everything. If any restore fails, containers stay stopped and a human must investigate.

**Container discovery**: Uses Docker Compose's built-in `com.docker.compose.project` label to discover containers at
runtime. Adding or removing services from Docker Compose requires zero changes to backup code.

## Running

```bash
make dev         # Start Dagster dev server (auto-reload)
make test        # Run pytest
make pr-ready    # Format + lint
```

**Dagster UI**: `http://localhost:3004`

- **Manual backup**: Assets tab → Materialize all
- **Restore**: Jobs → `full_restore_job` → select backup timestamp → Launch
- **Schedule**: Schedules tab → toggle `daily_backup_schedule` (2 AM Europe/Zurich)

## Configuration

Environment variables in `.env.dev` / `.env.prod`:

| Variable                | Default   | Purpose                                     |
| ----------------------- | --------- | ------------------------------------------- |
| `BACKUP_RETENTION_DAYS` | `7`       | Days to keep backups before auto-delete     |
| `BACKUP_MINIMUM_KEEP`   | `3`       | Minimum backups preserved regardless of age |
| `BACKUP_S3_BUCKET`      | `backups` | S3 bucket name for backup storage           |

Database credentials are inherited from the same environment variables used by the platform services.

## Implementation notes

**¹ DocumentDB catalog separate dump/restore**: The FerretDB PostgreSQL host uses the DocumentDB extension, which owns
its catalog tables (`documentdb_api_catalog.collections`, `collection_indexes`, and their sequences). PostgreSQL's
`pg_dump` skips data for extension-owned tables by default — it expects `CREATE EXTENSION` to repopulate them. The usual
fix (`pg_extension_config_dump()`) cannot be called externally — PostgreSQL restricts it to `CREATE EXTENSION` scripts.
These catalogs contain user-generated metadata (collection-to-table mappings, index definitions) that the extension
cannot reconstruct. During backup, the handler separately dumps catalog data using `COPY TO STDOUT` into an
`ext-catalog.sql.gz` artifact. During restore, this SQL is replayed after `pg_restore` to repopulate the catalog.
Without this step, restores would have the document data but an empty catalog — FerretDB would see no collections. See
`_DOCUMENTDB_CATALOG_TABLES` and `_DOCUMENTDB_CATALOG_SEQUENCES` in `services/postgres.py`.

## Adding a new service

See the `add-backup-service` skill (`.claude/skills/add-backup-service/SKILL.md`) for the step-by-step guide covering
all 9 registration points.
