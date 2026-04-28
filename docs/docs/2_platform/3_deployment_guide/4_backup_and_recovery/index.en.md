---
title: Backup and Recovery
---

# Backup and Recovery

## Overview

Swiss AI Hub includes an automated backup service that periodically dumps all stateful services to the internal
SeaweedFS S3 storage (`s3://backups/`). Backups run on a daily schedule (1 AM Europe/Zurich) with automatic retention
cleanup. The backup service is a standalone Dagster instance with a web UI for monitoring, manual triggers, and
parameterized restores.

Each instance has independent backups. Data isolation between instances. Recovery operations don't affect other
instances.

::: info Multi-instancing context
This chapter assumes a multi-instance deployment model where each organization has their own isolated Swiss AI Hub
instance. For multi-tenancy (logical separation within a single instance), see [Multi-tenancy](../../16_multi_tenancy/).
:::

______________________________________________________________________

## What gets backed up

| Service               | Method                                                   | Data                                              |
| --------------------- | -------------------------------------------------------- | ------------------------------------------------- |
| PostgreSQL (main)     | `pg_dumpall` + `pg_dump`                                 | OpenWebUI, Langfuse, Dagster, LiteLLM databases   |
| PostgreSQL (FerretDB) | `pg_dumpall` + `pg_dump` + `COPY` (DocumentDB catalog\*) | Agent configs, users, threads, tokens, RBAC roles |
| Milvus                | `milvus-backup` (official tool)                          | Vector collections with consistent metadata       |
| Neo4j                 | `neo4j-admin` via temp container                         | Agent memory graphs (Mem0)                        |
| ClickHouse            | `BACKUP TO Disk('backup_s3', ...)` SQL command           | Langfuse traces, observations, scores             |
| Valkey                | `BGSAVE` + RDB copy (+ temp container on restore)        | Cache and session state (RDB snapshot)            |
| NATS                  | `nats` CLI stream backup                                 | JetStream streams                                 |

### What is NOT backed up by the platform

**SeaweedFS bucket data** (user-uploaded documents, knowledge base files, chat attachments) is the responsibility of the
infrastructure layer. Use VM snapshots, rclone sync, or external S3 replication to protect this data. The platform
cannot back up SeaweedFS into itself.

All service backups are required. A missing backup for any service will block the restore.

______________________________________________________________________

## Configuration

Configure the backup service via environment variables in `.env.dev` (development) or `.env.prod` (production):

```bash
BACKUP_RETENTION_DAYS="7"            # Keep backups for N days (dev: 7, prod: 30)
BACKUP_MINIMUM_KEEP="3"             # Minimum backups preserved regardless of age
BACKUP_S3_BUCKET="backups"           # S3 bucket name for backup storage
```

The backup schedule (daily at 1 AM Europe/Zurich) is defined in Dagster and can be toggled on/off via the Dagster UI.

::: warning Backup and pipeline schedules must not overlap
The backup stops all application containers, including the pipeline Dagster instance. The default schedules are
staggered: backup at 1:00 AM, pipeline observation at 2:00 AM, pipeline cleanup at 3:00 AM. If you change any schedule,
ensure the backup finishes before the first pipeline job starts — a backup running during a pipeline job kills it
mid-execution.
:::

______________________________________________________________________

## How backups work

Every backup stops all managed containers in parallel before taking snapshots, guaranteeing transactional consistency
across all databases. Containers with the prefixes `backup-`, `seaweedfs-`, `etcd`, and `traefik` are excluded from the
stop/start cycle — SeaweedFS is needed for S3 access, etcd for Milvus metadata, and Traefik for ingress availability
during backups.

Each service is dumped using its native backup tool. After all services are backed up, the platform restarts all
previously running containers in parallel. Docker Compose restart policies ensure services converge to a healthy state
even if some start before their dependencies are ready. If the backup fails mid-run, a failure hook automatically
restarts all managed containers as a safety measure.

To trigger a manual backup, open the Dagster UI at `http://localhost:3004`, navigate to the backup assets, and click
"Materialize".

### Neo4j sibling container

Neo4j Community Edition does not support online backups — `neo4j-admin database dump` requires exclusive access to the
`/data` directory and cannot run while the Neo4j process holds a lock on it. Because a stopped Docker container cannot
execute commands either, the backup service spins up a **temporary sibling container** using the same Neo4j image and
the same `/data` volume (both discovered automatically from the production container at runtime). The sibling runs
`neo4j-admin`, copies the dump file out, and is removed immediately afterward. A similar sibling is used for restore.

You may notice a short-lived container named `neo4j-dump-<id>` or `neo4j-restore-<id>` during backup/restore runs — this
is expected and cleaned up automatically.

### \* DocumentDB catalog workaround

PostgreSQL's `pg_dump` silently skips data for tables owned by extensions — it assumes `CREATE EXTENSION` will
repopulate them during restore. The DocumentDB extension (used by FerretDB's PostgreSQL backend) owns its catalog tables
(`documentdb_api_catalog.collections` and `collection_indexes`) but does not register them for dump inclusion. The usual
fix (`pg_extension_config_dump()`) cannot be called externally — PostgreSQL restricts it to `CREATE EXTENSION` scripts.

Without a workaround, a restore would have all document data intact but an empty catalog — FerretDB would report zero
collections. The backup service handles this automatically: during backup it separately extracts catalog rows using
`COPY TO STDOUT` into an `ext-catalog.sql.gz` artifact, and during restore it replays this SQL after `pg_restore`. No
operator action is required.

______________________________________________________________________

## Listing backups

Open the Dagster UI at `http://localhost:3004` to see the backup asset view, which shows backup history at a glance. The
asset metadata includes timestamp and S3 prefix for each backup.

______________________________________________________________________

## Recovery

### Full-system restore

Restores the entire platform to a specific backup. Stops all services, restores each database, then restarts all
containers.

To run a full restore, open the Dagster UI at `http://localhost:3004`, navigate to Jobs -> `full_restore_job`, select a
backup timestamp from the partition dropdown, and click "Launch Run".

The restore process follows three phases:

1. **Full stop**: All application and database containers are stopped (except SeaweedFS, which is needed for S3 access)
2. **Restore data**: Each service is restored from its backup. PostgreSQL instances are started temporarily for SQL
   import. Milvus is started temporarily for the milvus-backup restore API.
3. **Full start**: All previously running containers are restarted. Docker Compose restart policies ensure services
   converge to a healthy state even if some start before their dependencies are ready.

::: warning Restore failure behavior
On failure during restore, containers are intentionally **not** restarted automatically. The operator must investigate
the failure and decide whether to retry or restore from a different backup. This is a deliberate safety measure — an
automatic restart after a partial restore could leave the system in an inconsistent state.
:::

______________________________________________________________________

## VM snapshots

VM snapshots remain a valid complementary strategy, especially for protecting SeaweedFS data. They capture everything:
OS, Docker, data, configuration. You restore the entire VM in one operation.

Stop Swiss AI Hub services before creating a snapshot using `docker compose down`. Alternatively, use
application-consistent snapshots (Azure with VM agent, VMware with quiesce). Create snapshots before major updates.

______________________________________________________________________

## Continuous Postgres maintenance

The same Dagster instance that runs backup also runs **continuous Postgres health maintenance** so the platform's
`event_logs` and `runs` tables don't grow without bound on long-running deployments. Two additional jobs are wired into
the same backup Dagster UI at `http://localhost:3004`:

- **`dagster_cleanup_job`** — Sundays at 3 AM Europe/Zurich. Prunes verbose Python logs and curated framework-internal
  events (`HANDLED_OUTPUT`, `LOADED_INPUT`, `ENGINE_EVENT`, `ASSET_MATERIALIZATION_PLANNED`, `STEP_OUTPUT`) past their
  retention windows. Idempotently ensures the cleanup query indexes exist and applies tighter autovacuum tuning to the
  heavy tables.
- **`postgres_repack_job`** — first Sunday of each month at 4 AM. Runs `pg_repack` on `event_logs`, `runs`, and
  `job_ticks` to return disk pages to the OS (plain `VACUUM` only marks dead rows reusable internally).

**UI-safe by construction**: cleanup never deletes rows the Dagster UI depends on (`ASSET_MATERIALIZATION`,
`STEP_SUCCESS`, `STEP_FAILURE`, `RUN_SUCCESS`, `RUN_FAILURE`, the `runs` table, asset catalog, sensor cursors).

**Mutually exclusive with backup**: every job that touches Postgres carries a `postgres-mutex` tag. The backup Dagster's
run coordinator caps concurrency for that tag at one, so cleanup or repack ticks queue behind a still-running backup
instead of starting concurrently. Within each run, intra-run parallelism (e.g. parallel per-service backups) is
unaffected.

**`pg_repack` ships in the platform Postgres image**: the project-managed image extends `pgvector/pgvector:pg17` with
`postgresql-17-repack` and the extension is registered in the `dagster` database on first init. Deployments using a
foreign Postgres image without the extension still work — repack reports a clean skip in the run metadata; cleanup works
unconditionally.

### Configuration

```bash
# Retention windows (defaults follow the official Dagster docs recipe)
DAGSTER_DEBUG_LOG_RETENTION_DAYS="7"
DAGSTER_INFO_LOG_RETENTION_DAYS="60"
DAGSTER_WARNING_LOG_RETENTION_DAYS="60"
DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS="30"

# Per-DELETE row cap — protects against WAL-flooding on first run against a backlogged DB
DAGSTER_CLEANUP_BATCH_LIMIT="1000000"

# Kill switch — set to true and the maintenance handlers no-op; backup is unaffected
MAINTENANCE_DISABLED="false"

DAGSTER_DB="dagster"
POSTGRES_PORT="5432"
```

A heavily backlogged DB drains over multiple weekly ticks (`DAGSTER_CLEANUP_BATCH_LIMIT` rows per tick × 4 cleanup
handlers). Operators wanting a faster initial drain can manually launch `dagster_cleanup_job` repeatedly through the
Dagster UI.

______________________________________________________________________

## Backup storage layout

Each backup is stored in a flat, timestamped directory:

```
s3://backups/
  2026-02-17_02-00-00/
    postgres-main/
      globals.sql.gz
      openwebui.dump
      langfuse.dump
      dagster.dump
      litellm.dump
    postgres-ferretdb/
      globals.sql.gz
      ferretdb.dump
      ext-catalog.sql.gz
    milvus_backup_2026_02_17_02_00_00/...
    neo4j.dump
    clickhouse/
      backup_2026_02_17_02_00_00/...
    valkey.rdb
    nats-jetstream.tar.gz
  2026-02-18_02-00-00/
    ...
```

______________________________________________________________________
