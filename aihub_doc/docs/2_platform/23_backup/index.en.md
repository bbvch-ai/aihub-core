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

## How backups work

Every backup stops all application services before taking snapshots, guaranteeing transactional consistency across all
databases. After all services are backed up, the platform restarts everything. Docker Compose restart policies ensure
services converge to a healthy state even if some start before their dependencies are ready. The brief downtime during
the daily 2 AM backup window is the trade-off for guaranteed consistency.

::: warning Neo4j always requires offline backup
Neo4j Community Edition does not support online backups. The backup service handles this automatically — Neo4j is
stopped and restarted during its backup window.
:::

## Scheduling and retention

The backup service runs a daily schedule at **2:00 AM** (Europe/Zurich timezone). You can enable or disable the schedule
through the Dagster UI without redeployment — the setting persists across container restarts.

**Retention policy**: Backups are automatically deleted after the configured retention period (default: 7 days in dev,
30 days in production). A minimum of 3 backups are always preserved regardless of age.

## Where backups are stored

All backup artifacts are stored in the platform's S3-compatible storage (SeaweedFS) under the `backups` bucket. Each
backup creates a timestamped directory:

```
s3://backups/2026-02-24_10-30-00/
s3://backups/2026-02-15_18-45-30/
```

## Restoring from backup

The platform supports full system restore, which recovers all services from a single backup. The service validates that
all backup files exist, stops the entire platform, restores each service, and restarts everything.

The restore job uses a **partition selector** — the Dagster UI shows a dropdown of all available backup timestamps, so
you can pick the exact backup to restore from without typing timestamps manually.

::: warning Partial failures halt the restore
If any service fails to restore, the entire run halts. Containers remain stopped and no automatic recovery is attempted
— a partially restored system is dangerous. A human must investigate the failure, fix the root cause, and re-run the
restore manually.
:::

## How it works

The backup service runs as an independent Dagster instance with its own SQLite storage. This is a deliberate design
choice: because the service backs up PostgreSQL, it cannot depend on PostgreSQL for its own state. Even if the main
database is unavailable, the backup service remains operational.

The service uses purpose-built tools for each database: `pg_dumpall` for PostgreSQL, the official `milvus-backup` tool
for vector data, `neo4j-admin` for graph exports, and native backup commands for ClickHouse, Valkey, and NATS. Each tool
is chosen for reliability and compatibility with the specific service's data format.

During restore operations, the service orchestrates container lifecycle through the Docker API — stopping all managed
services, restoring data using each service's native tool, and restarting containers. Docker Compose restart policies
ensure services converge to a healthy state.

## Managing backups through the UI

The backup service exposes a Dagster web interface for monitoring and manual operations:

- **Assets tab**: View backup history across all services. Trigger manual backups by materializing the backup assets.
- **Schedules tab**: Enable or disable the daily 2 AM backup schedule. View upcoming and past scheduled runs.
- **Jobs tab**: Launch restore operations. Select a backup timestamp from the partition dropdown and launch.
- **Runs tab**: Monitor active backup and restore operations with real-time progress. Review logs from completed runs to
  verify success or diagnose failures.

::: details Access URL
The Dagster UI is available at `http://localhost:3004` in development. In production, it is exposed through Traefik with
the same authentication as other platform services.
:::

## Configuration

The backup service is configured through environment variables in `.env.dev` or `.env.prod`. Key settings:

| Variable                | Default   | Purpose                                     |
| ----------------------- | --------- | ------------------------------------------- |
| `BACKUP_RETENTION_DAYS` | `7`       | Days to keep backups before auto-delete     |
| `BACKUP_MINIMUM_KEEP`   | `3`       | Minimum backups preserved regardless of age |
| `BACKUP_S3_BUCKET`      | `backups` | S3 bucket name for backup storage           |

Database credentials (PostgreSQL, Milvus, ClickHouse, Valkey, NATS) are inherited from the same environment variables
used by the platform services themselves.

## Recovery considerations

A few things to keep in mind when planning for disaster recovery:

- **Milvus collections are not loaded into memory after restore.** Applications automatically load collections on
  startup, so a full service restart handles this. No manual intervention is needed.
- **Test your restores.** A backup is only as good as its last successful restore. Periodically verify that restore
  operations complete successfully in a staging environment.
