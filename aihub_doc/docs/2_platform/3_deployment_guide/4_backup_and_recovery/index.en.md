---
title: Backup and Recovery
---

# Backup and Recovery

## Overview

Each instance has independent backups. Data isolation between instances. Recovery operations don't affect other
instances.

::: info Multi-instancing context
This chapter assumes a multi-instance deployment model where each organization has their own isolated AI-Hub instance.
For multi-tenancy (logical separation within a single instance), see [Multi-tenancy](../../16_multi_tenancy/).
:::

## Backup approaches

You can back up the AI-Hub using VM snapshots or component-level backups.

VM snapshots capture the entire virtual machine state. You restore the whole system at once. Component-level backups
handle individual data stores separately, so you can restore specific parts.

---

## VM snapshots

VM snapshots capture everything: OS, Docker, data, configuration. You restore the entire VM in one operation. No backup
scripts needed. All services are consistent at the same point in time.

Backup sizes are large since you're copying the entire disk. Backup times are longer. You can't selectively restore
individual databases. The VM needs to be stopped, or you need a snapshot-capable hypervisor.

Stop AI-Hub services before creating a snapshot using `docker compose down`. Alternatively, use application-consistent
snapshots (Azure with VM agent, VMware with quiesce). Create snapshots before major updates. Test restores regularly.

---

## Component-level backups

### What to back up

PostgreSQL stores multiple databases: OpenWebUI, Langfuse, Dagster, and LiteLLM. A separate PostgreSQL instance stores
the FerretDB backend. Use pg_basebackup for full backups and WAL archiving for point-in-time recovery.

FerretDB stores agent configurations, process definitions, chat histories, user sessions, and knowledge base metadata.
The PostgreSQL backup for the FerretDB instance covers this. You can optionally create MongoDB-format exports for
portability.

Milvus stores vector embeddings for RAG. Export collections to S3-compatible storage. Embeddings can be regenerated from
source documents if needed.

SeaweedFS stores user-uploaded documents, RAG knowledge base files, and chat attachments. The SeaweedFS Filer uses etcd
for metadata storage (backed up with etcd snapshots below). Back up the actual file data using S3-compatible sync tools.

Valkey stores cache data and WebSocket session state for OpenWebUI. Valkey persists to disk automatically. Back up the
data volume.

NATS stores event streams and message persistence for the event-driven architecture. Back up the data volume.

etcd stores Milvus coordination metadata, SeaweedFS Filer metadata, and service discovery information. Use
snapshot-based backup.

Configuration includes environment variables, SSL certificates, and Docker compose files. Encrypt backups. Store
encryption keys separately (HSM, key management services, multiple secure locations).

---

## Backup automation

Automate backup tasks with cron or similar schedulers. Schedule backups during low-usage periods to avoid performance
impact. Verify backup integrity regularly and alert on failures.

---
