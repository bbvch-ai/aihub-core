---
title: Backup and restore
---

# Backup and restore

Self-hosted platforms need reliable backups. The Swiss AI-Hub includes a centralized backup service that protects all
stateful infrastructure — databases, vector stores, caches, and message streams — with daily automated backups and
on-demand restore capabilities.

## What gets backed up

The backup service covers every stateful service in the platform:

| Service    | What it stores                                             |
| ---------- | ---------------------------------------------------------- |
| PostgreSQL | User accounts, chat history, cost tracking, pipeline state |
| FerretDB   | Conversations, agent configurations, process definitions   |
| Milvus     | Vector embeddings for knowledge retrieval and RAG          |
| Neo4j      | Graph-based agent memory and knowledge relationships       |
| ClickHouse | Analytics data for Langfuse observability                  |
| Valkey     | Ephemeral agent state and session caches                   |
| NATS       | JetStream event streams for the Swiss AI Agent Protocol    |

::: details What about file storage?
SeaweedFS (the platform's S3-compatible object store) is deliberately excluded. Large binary storage is better protected
at the infrastructure level through VM snapshots or off-site S3 replication, rather than application-level backup.
:::

## Two backup modes

**Online backups** run against the live system with no downtime. The platform continues serving requests while backups
execute in the background. Daily scheduled backups always use online mode. Consistency is best-effort — applications may
write during the backup window — but for most workloads this is perfectly adequate.

**Offline backups** stop all services before taking snapshots, guaranteeing transactional consistency. Use offline mode
before major upgrades, for compliance requirements, or whenever you need a precise point-in-time snapshot. The trade-off
is brief downtime while services stop, back up, and restart.

::: warning Neo4j always requires offline backup
Neo4j Community Edition does not support online backups. The backup service handles this automatically — even in online
mode, Neo4j is briefly stopped and restarted during its backup window.
:::

## Scheduling and retention

The backup service runs a daily schedule at **2:00 AM** (Europe/Zurich timezone) using online mode. You can enable or
disable the schedule through the Dagster UI without redeployment — the setting persists across container restarts.

**Retention policy**: Online backups are automatically deleted after 7 days (configurable via `BACKUP_RETENTION_DAYS`).
Offline backups are never automatically deleted, since they represent deliberate point-in-time snapshots typically kept
for compliance or disaster recovery.

## Where backups are stored

All backup artifacts are stored in the platform's S3-compatible storage (SeaweedFS) under the `backups` bucket. Each
backup creates a timestamped directory:

```
s3://backups/2026-02-24_10-30-00_online/
s3://backups/2026-02-15_18-45-30_offline/
```

The timestamp and mode in the directory name make it easy to identify and manage backups. When both online and offline
backups exist, restore operations prefer the offline version for stronger consistency.

## Restoring from backup

The platform supports two restore strategies:

**Full system restore** recovers all services from a single backup. The service validates that all backup files exist,
stops the entire platform in dependency order, restores each service, and restarts everything with health checks. If no
timestamp is specified, the most recent backup is used automatically.

**Single service restore** targets one database without restoring the entire platform. Use this when only one service
has issues — for example, recovering ClickHouse analytics data without affecting conversations or vector embeddings.

::: details Force mode for partial failures
By default, a restore aborts at the first service failure to prevent inconsistent state. Enable force mode to continue
past individual failures — the service logs errors but proceeds with remaining services. Use this when you need a
best-effort recovery and can tolerate some services restoring from a different backup.
:::

## How it works

The backup service runs as an independent Dagster instance with its own SQLite storage. This is a deliberate design
choice: because the service backs up PostgreSQL, it cannot depend on PostgreSQL for its own state. Even if the main
database is unavailable, the backup service remains operational.

The service uses purpose-built tools for each database: `pg_dumpall` for PostgreSQL, the official `milvus-backup` tool
for vector data, `neo4j-admin` for graph exports, and native backup commands for ClickHouse, Valkey, and NATS. Each tool
is chosen for reliability and compatibility with the specific service's data format.

During restore operations, the service orchestrates container lifecycle through the Docker API — stopping services in
dependency order, restoring data, and restarting with health check verification. Infrastructure services start first
(databases), followed by consumers (vector store, cache, message broker), and finally application services.

## Managing backups through the UI

The backup service exposes a Dagster web interface for monitoring and manual operations:

- **Assets tab**: View backup history across all services. Trigger manual backups by selecting a date partition and
  choosing online or offline mode.
- **Schedules tab**: Enable or disable the daily 2 AM backup schedule. View upcoming and past scheduled runs.
- **Jobs tab**: Launch restore operations through the Launchpad. Specify a timestamp and service name for targeted
  restores, or run a full system restore.
- **Runs tab**: Monitor active backup and restore operations with real-time progress. Review logs from completed runs to
  verify success or diagnose failures.

::: details Access URL
The Dagster UI is available at `http://localhost:3004` in development. In production, it is exposed through Traefik with
the same authentication as other platform services.
:::

## Configuration

The backup service is configured through environment variables in `.env.dev` or `.env.prod`. Key settings:

| Variable                     | Default   | Purpose                                        |
| ---------------------------- | --------- | ---------------------------------------------- |
| `BACKUP_RETENTION_DAYS`      | `7`       | Days to keep online backups before auto-delete |
| `BACKUP_SKIP_MILVUS_ONLINE`  | `false`   | Skip Milvus in online backups                  |
| `BACKUP_SKIP_MILVUS_OFFLINE` | `false`   | Skip Milvus in offline backups                 |
| `BACKUP_S3_BUCKET`           | `backups` | S3 bucket name for backup storage              |

Database credentials (PostgreSQL, Milvus, ClickHouse, Valkey, NATS) are inherited from the same environment variables
used by the platform services themselves.

## Recovery considerations

A few things to keep in mind when planning for disaster recovery:

- **Milvus collections are not loaded into memory after restore.** Applications automatically load collections on
  startup, so a full service restart handles this. No manual intervention is needed.
- **Offline backups are stronger for compliance.** If you need to prove exact point-in-time recovery for auditing or
  regulatory purposes, schedule periodic offline backups in addition to the daily online backups.
- **Test your restores.** A backup is only as good as its last successful restore. Periodically verify that restore
  operations complete successfully in a staging environment.
