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

| Service               | Method                          | Online?         | Data                                              |
| --------------------- | ------------------------------- | --------------- | ------------------------------------------------- |
| PostgreSQL (main)     | `pg_dumpall`                    | Yes             | OpenWebUI, Langfuse, Dagster, LiteLLM databases   |
| PostgreSQL (FerretDB) | `pg_dumpall`                    | Yes             | Agent configs, users, threads, tokens, RBAC roles |
| Milvus                | `milvus-backup` (official tool) | Yes             | Vector collections with consistent metadata       |
| Neo4j                 | `neo4j-admin database dump`     | No (brief stop) | Agent memory graphs (Mem0)                        |
| ClickHouse            | `clickhouse-client` BACKUP      | Yes             | Langfuse traces, observations, scores             |
| Valkey                | `BGSAVE` + RDB copy             | Yes             | Cache and session state (RDB snapshot)            |
| NATS                  | `nats` CLI stream backup        | Yes             | JetStream streams                                 |

### What is NOT backed up by the platform

**SeaweedFS bucket data** (user-uploaded documents, knowledge base files, chat attachments) is the responsibility of the
infrastructure layer. Use VM snapshots, rclone sync, or external S3 replication to protect this data. The platform
cannot back up SeaweedFS into itself.

Valkey and NATS backups are non-critical — missing backups produce warnings, not errors. Valkey stores cache and session
state that rebuilds on restart. NATS stores transient messages; important events are already persisted in FerretDB.

______________________________________________________________________

## Configuration

Configure the backup service via environment variables in `.env`:

```bash
BACKUP_RETENTION_DAYS="7"            # Keep online backups for N days (dev: 7, prod: 30)
BACKUP_SKIP_MILVUS_ONLINE="false"    # Skip Milvus in online backups (large vector data)
BACKUP_SKIP_MILVUS_OFFLINE="false"   # Skip Milvus in offline backups
```

The backup schedule (daily at 2 AM Europe/Zurich) is defined in Dagster and can be toggled on/off via the Dagster UI.

Offline backups are never auto-deleted by retention cleanup and are preserved indefinitely.

______________________________________________________________________

## Backup modes

### Online backup (default)

Each service is dumped individually without stopping application services. Per-service dumps are internally consistent
(PostgreSQL uses MVCC, milvus-backup flushes and pauses GC). Minor cross-service drift is possible within the ~1-2
minute backup window.

To trigger a manual online backup, open the Dagster UI at `http://localhost:3004`, navigate to the backup asset, and
click "Materialize".

### Offline backup (manual)

Stops all application services before running backups, guaranteeing perfect cross-service consistency. Use this before
major upgrades or when a known-good snapshot is needed.

To trigger an offline backup, launch the `backup_asset_job` from the Dagster UI Launchpad with `mode: "offline"`.

Neo4j requires a brief container stop even in online mode because Neo4j Community Edition does not support online
backups.

______________________________________________________________________

## Listing backups

Open the Dagster UI at `http://localhost:3004` to see the backup asset calendar view, which shows daily backup coverage
at a glance. The asset metadata includes timestamp, mode, and S3 prefix for each backup.

______________________________________________________________________

## Recovery

### Full-system restore

Restores the entire platform to a specific backup. Stops all services, restores each database, then restarts everything
in dependency order with health checks.

To run a full restore, open the Dagster UI at `http://localhost:3004`, navigate to Jobs → `full_restore_job` →
Launchpad, enter the backup timestamp, and click "Launch Run".

The restore process follows three phases:

1. **Full stop**: All application and database containers are stopped (except SeaweedFS, which is needed for S3 access)
2. **Restore data**: Each service is restored from its backup. PostgreSQL instances are started temporarily for SQL
   import. Milvus is started temporarily for the milvus-backup restore API.
3. **Full start**: All containers are started in dependency order (infrastructure first, then databases, then
   applications). Health checks verify each service.

### Per-service restore

For targeted recovery of individual services, use Jobs → `single_service_restore_job` → Launchpad in the Dagster UI.
Enter the service name and optionally a timestamp (defaults to the latest backup).

______________________________________________________________________

## VM snapshots

VM snapshots remain a valid complementary strategy, especially for protecting SeaweedFS data. They capture everything:
OS, Docker, data, configuration. You restore the entire VM in one operation.

Stop AI-Hub services before creating a snapshot using `docker compose down`. Alternatively, use application-consistent
snapshots (Azure with VM agent, VMware with quiesce). Create snapshots before major updates.

______________________________________________________________________

## Backup storage layout

Each backup is stored in a flat, timestamped directory with the mode (online/offline) in the name:

```
s3://backups/
  2026-02-17_02-00-00_online/
    postgres-main.sql.gz
    postgres-ferretdb.sql.gz
    backup_2026_02_17_02_00_00/...       (Milvus backup)
    neo4j.dump
    clickhouse.tar.gz
    valkey.rdb
    nats-jetstream.tar.gz
  2026-02-18_03-00-00_offline/
    postgres-main.sql.gz
    postgres-ferretdb.sql.gz
    backup_2026_02_18_03_00_00/...
    neo4j.dump
    clickhouse.tar.gz
    valkey.rdb
    nats-jetstream.tar.gz
```

______________________________________________________________________
