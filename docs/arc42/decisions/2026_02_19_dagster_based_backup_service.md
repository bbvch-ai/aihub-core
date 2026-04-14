# Independent Dagster-Based Backup Service

## Context

Swiss AI Hub requires centralized backup and restore for all stateful services: PostgreSQL (x2), Milvus, Neo4j,
ClickHouse, Valkey, and NATS JetStream. Building this service requires scheduling (daily backups at 1 AM Europe/Zurich),
job tracking (run history, success/failure, duration), progress monitoring, parameterized restores, and a web-accessible
interface for operators.

A custom stack — FastAPI REST API, APScheduler for cron scheduling, an in-memory job manager for async tracking, and API
key auth — could provide these capabilities, but would mean ~650 lines of infrastructure code unrelated to the actual
backup logic.

The platform already runs a Dagster instance for data pipelines (`packages/pipeline`), backed by a shared PostgreSQL
database. The question was whether the backup service should reuse that Dagster instance, run its own, or use a
non-Dagster approach entirely.

Separately, etcd is deployed as part of the Milvus cluster (metadata store) and does not have its own explicit backup
procedure. This was a deliberate decision that needed to be documented.

## Decision Drivers

- **Operational visibility**\
  Backups are critical operations that need run history, success/failure tracking, duration metrics, and a calendar view
  of what was backed up when. A custom job manager would store runs in-memory — lost on restart.

- **Scheduling with timezone support**\
  Backups must run at 1 AM Europe/Zurich daily. APScheduler can handle this but requires manual cron parsing and has no
  UI to inspect or toggle schedules.

- **Parameterized restores**\
  Restores need user-provided config (timestamp, optional service filter). A custom API would require building request
  schemas and validation; Dagster's Launchpad provides this out of the box.

- **Independence from shared infrastructure**\
  The backup service must not depend on the very databases it is backing up. If PostgreSQL is down, the backup service
  must still be able to report status, show run history, and accept restore commands.

- **Minimal maintenance burden**\
  A custom stack (FastAPI + APScheduler + job manager + API key auth) would be ~650 lines of infrastructure code
  unrelated to the actual backup logic. Dagster replaces all of it with declarative definitions.

- **etcd is not application data**\
  etcd stores Milvus cluster metadata (collection schemas, indexes, partition info). The `milvus-backup` tool captures
  this metadata as part of its backup process. The raw etcd data is not useful without a running Milvus instance, and
  restoring Milvus from `milvus-backup` fully recreates the etcd state. Backing up etcd separately would be redundant.

## Decision

### Standalone Dagster instance with SQLite storage

The backup service runs its own Dagster instance (webserver + daemon) with the default SQLite storage backend. It does
not share the PostgreSQL-backed Dagster instance used by `packages/pipeline`.

**Architecture**:

- Three containers following Dagster best practices: `backup-code` (gRPC code server, executes runs), `backup-daemon`
  (schedule/sensor management), `backup-webserver` (UI on port 3000, mapped to 3004 on host)
- Dagster state (run history, event logs, schedule state) is stored in SQLite at `$DAGSTER_HOME` in a shared volume
- The workspace loads `swiss_ai_hub.backup.dagster` as the sole code location
- The `backup-code` container mounts the Docker socket (`/var/run/docker.sock:ro`) to manage sibling containers
  (stop/start services, exec in containers, create temp containers for Neo4j/Valkey)

**Backup model**:

- Backups are modeled as a fan-out asset graph: a session root asset fans out to six per-service assets (PostgreSQL,
  Milvus, Neo4j, ClickHouse, Valkey, NATS), which fan in to a finalize asset
- A `DynamicPartitionsDefinition` tracks available backup timestamps (synced from S3 after each backup)
- A `daily_backup_schedule` triggers backups at 1 AM Europe/Zurich
- Restores use `full_restore_job` with a partition selector showing available backup timestamps in the Dagster Launchpad
- Container stop/start is parallelized via `ThreadPoolExecutor` for faster backup cycles
- Containers with prefixes `backup-`, `seaweedfs-`, `etcd`, and `traefik` are excluded from the stop/start cycle
- A failure hook automatically restarts all managed containers if the backup fails mid-run

**Why not share the pipeline Dagster instance**:

- The backup service backs up PostgreSQL — it cannot depend on PostgreSQL for its own state
- Isolating the backup service means it can start, show history, and accept restores even when other infrastructure is
  degraded
- Different operational lifecycle — backup schedules and runs are unrelated to data pipeline runs and should not clutter
  the same UI
- No cross-dependency on shared dagster-postgres config, PgBouncer, or database migrations

### No explicit etcd backup

etcd is not backed up as a separate service. This is safe because:

- **Milvus metadata is captured by `milvus-backup`**: The official Zilliz backup tool exports collection schemas,
  indexes, partitions, and segment metadata. Restoring from a `milvus-backup` snapshot fully reconstructs the etcd state
  that Milvus needs.
- **etcd data alone is not useful**: Raw etcd key-value pairs are tightly coupled to Milvus internals. A standalone etcd
  backup cannot be meaningfully restored without the corresponding Milvus data files.
- **S3 object data is out of scope**: etcd also references S3 object paths for Milvus segment data. The S3 storage layer
  (SeaweedFS) is the responsibility of infrastructure-level backup (VM snapshots, rclone, off-site S3 replication).

## Consequences

### Positive

- Run history persists across container restarts (SQLite file at `$DAGSTER_HOME`)
- Calendar-based partition view shows daily backup coverage at a glance
- Schedules can be toggled on/off via the UI without redeployment
- Restores are self-service via the Launchpad — no curl/API key required
- Avoided ~650 lines of custom infrastructure code (API, scheduler, job manager, auth)
- Backup service starts and operates independently of all backed-up databases
- No etcd backup complexity — `milvus-backup` already covers the Milvus metadata layer

### Trade-offs

- SQLite run history is lost if the container volume is not persisted. Acceptable because backup artifacts live in S3
  and run history is operational, not critical data.
- Dagster adds ~200 MB to the container image compared to a lean FastAPI stack. Acceptable given the operational
  benefits.
- The Dagster UI port (3004) is only exposed in dev/local/build stages. Production access is through an OAuth2 proxy
  sidecar behind Traefik.
- Two Dagster instances in the platform (pipeline + backup) means two UIs to monitor. This is intentional — they serve
  different operational concerns.
- The backup container requires the Docker socket (`/var/run/docker.sock`) mounted to manage sibling containers
  (stop/start Neo4j, exec in ClickHouse/Valkey, create temp containers for neo4j-admin).
