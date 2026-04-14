# Independent Dagster-Based Backup Service

## Context

Swiss AI Hub needs centralized backup/restore for all stateful services (PostgreSQL x2, Milvus, Neo4j, ClickHouse,
Valkey, NATS JetStream). This requires scheduling, run history, parameterized restores, and a web UI. A custom stack
(FastAPI + APScheduler + job manager) would be ~650 lines of infrastructure unrelated to backup logic. The platform
already runs Dagster for data pipelines.

## Decision Drivers

- **Independence from backed-up databases**\
  The backup service backs up PostgreSQL — it cannot depend on PostgreSQL for its own state.
- **Operational visibility**\
  Run history, success/failure tracking, and schedule management need a persistent UI, not in-memory state.
- **Minimal custom code**\
  Dagster replaces scheduling, job tracking, parameterized runs, and a web UI with declarative definitions.
- **etcd is redundant to back up**\
  `milvus-backup` captures all Milvus metadata. Raw etcd data is not useful without corresponding Milvus data files.

## Decision

Standalone Dagster instance with SQLite storage (3 containers: `backup-code`, `backup-daemon`, `backup-webserver`),
separate from the pipeline Dagster instance. Fan-out asset graph: session → 6 per-service assets → finalize. Daily
schedule at 1 AM Europe/Zurich. Restores via partition selector in the Dagster Launchpad. Container stop/start
parallelized via `ThreadPoolExecutor`. Failure hook restarts all managed containers. etcd is not backed up separately.

## Consequences

### Positive

- Persistent run history, self-service restores, toggleable schedules — no custom code
- Backup service operates independently of all backed-up databases
- No etcd backup complexity

### Trade-offs

- SQLite run history lost if volume not persisted (acceptable — artifacts live in S3)
- Two Dagster instances to monitor (intentional — different operational concerns)
- Docker socket required for container management
