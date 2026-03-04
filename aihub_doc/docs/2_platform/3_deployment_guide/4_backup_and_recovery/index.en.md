---
title: Backup and Recovery
---

# Backup and Recovery

## Overview

AI-Hub includes an automated backup service that periodically dumps all stateful services to the internal SeaweedFS S3
storage (`s3://backups/`). Backups run on a daily schedule (2 AM Europe/Zurich) with automatic retention cleanup. The
backup service is a standalone Dagster instance with a web UI for monitoring, manual triggers, and parameterized
restores.

Each instance has independent backups. Data isolation between instances. Recovery operations don't affect other
instances.

::: info Multi-instancing context
This chapter assumes a multi-instance deployment model where each organization has their own isolated AI-Hub instance.
For multi-tenancy (logical separation within a single instance), see [Multi-tenancy](../../16_multi_tenancy/).
:::

______________________________________________________________________

## What gets backed up

| Service               | Method                                                  | Data                                              |
| --------------------- | ------------------------------------------------------- | ------------------------------------------------- |
| PostgreSQL (main)     | `pg_dumpall` + `pg_dump`                                | OpenWebUI, Langfuse, Dagster, LiteLLM databases   |
| PostgreSQL (FerretDB) | `pg_dumpall` + `pg_dump` + `COPY` (DocumentDB catalog¹) | Agent configs, users, threads, tokens, RBAC roles |
| Milvus                | `milvus-backup` (official tool)                         | Vector collections with consistent metadata       |
| Neo4j                 | `neo4j-admin` via temp container                        | Agent memory graphs (Mem0)                        |
| ClickHouse            | `BACKUP TO S3()` SQL command                            | Langfuse traces, observations, scores             |
| Valkey                | `BGSAVE` + RDB copy (+ temp container on restore)       | Cache and session state (RDB snapshot)            |
| NATS                  | `nats` CLI stream backup                                | JetStream streams                                 |

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

The backup schedule (daily at 2 AM Europe/Zurich) is defined in Dagster and can be toggled on/off via the Dagster UI.

______________________________________________________________________

## How backups work

Every backup stops all managed containers before taking snapshots, guaranteeing transactional consistency across all
databases. Each service is dumped using its native backup tool. After all services are backed up, the platform restarts
all previously running containers. Docker Compose restart policies ensure services converge to a healthy state even if
some start before their dependencies are ready.

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

### ¹ DocumentDB catalog workaround

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

To run a full restore, open the Dagster UI at `http://localhost:3004`, navigate to Jobs → `full_restore_job`, select a
backup timestamp from the partition dropdown, and click "Launch Run".

The restore process follows three phases:

1. **Full stop**: All application and database containers are stopped (except SeaweedFS, which is needed for S3 access)
2. **Restore data**: Each service is restored from its backup. PostgreSQL instances are started temporarily for SQL
   import. Milvus is started temporarily for the milvus-backup restore API.
3. **Full start**: All previously running containers are restarted. Docker Compose restart policies ensure services
   converge to a healthy state even if some start before their dependencies are ready.

______________________________________________________________________

## VM snapshots

VM snapshots remain a valid complementary strategy, especially for protecting SeaweedFS data. They capture everything:
OS, Docker, data, configuration. You restore the entire VM in one operation.

Stop AI-Hub services before creating a snapshot using `docker compose down`. Alternatively, use application-consistent
snapshots (Azure with VM agent, VMware with quiesce). Create snapshots before major updates.

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
