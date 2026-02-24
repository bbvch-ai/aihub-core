# aihub_backup - Backup & Restore Service

**Purpose**: Centralized backup and restore for all AI-Hub data services. Runs as a Dagster-based container with a web
UI for monitoring, scheduling, and parameterized job execution.

## Scope Responsibility

Backup and restore orchestration for PostgreSQL (x2), Milvus, Neo4j, ClickHouse, Valkey (Redis), and NATS JetStream. S3
storage via SeaweedFS. Retention policy enforcement. No dependency on `aihub_lib` — fully self-contained.

## Architecture

- **Dagster Webserver**: Web UI + GraphQL API on port 3000 (mapped to 3004 on host) for monitoring, manual triggers, and
  parameterized restores
- **Dagster Daemon**: Background process for schedule execution and run monitoring
- **Assets**: Daily-partitioned multi-asset (`create_backup`) producing 6 service backup artifacts with calendar view
- **Jobs**: Parameterized restore jobs (`full_restore_job`, `single_service_restore_job`) with config via Dagster
  Launchpad
- **Schedule**: Daily online backup at 2 AM Europe/Zurich (`daily_backup_schedule`)
- **Services**: Per-database handlers (postgres, milvus, neo4j, clickhouse, valkey, nats) implementing a common
  `BackupHandler` ABC
- **S3**: boto3 client for SeaweedFS S3-compatible storage
- **Docker**: Docker SDK for container lifecycle management (stop/start/exec/cp)

## Folder Structure

```
aihub_backup/
├── aihub_backup/
│   ├── settings.py          # Pydantic settings (env vars)
│   ├── s3.py                # boto3 S3 wrapper
│   ├── docker_client.py     # Docker SDK wrapper
│   ├── models.py            # Data models (BackupMode, ServiceResult, etc.)
│   ├── orchestrator.py      # Backup/restore orchestration
│   ├── retention.py         # Retention cleanup
│   ├── dagster/
│   │   ├── __init__.py      # Dagster Definitions (code location entry point)
│   │   ├── config.py        # BackupConfig, RestoreConfig, SingleServiceRestoreConfig
│   │   ├── resources.py     # ConfigurableResource wrappers for existing classes
│   │   ├── assets.py        # @multi_asset create_backup (daily partitioned)
│   │   ├── jobs.py          # backup_asset_job, full_restore_job, single_service_restore_job
│   │   ├── schedules.py     # daily_backup_schedule (2 AM Zurich)
│   │   └── ops/
│   │       └── restore_ops.py  # run_full_restore, run_single_service_restore
│   └── services/
│       ├── base.py          # BackupHandler ABC
│       ├── postgres.py      # pg_dumpall/psql
│       ├── milvus.py        # milvus-backup binary
│       ├── neo4j.py         # neo4j-admin via Docker SDK
│       ├── clickhouse.py    # clickhouse-connect + Docker SDK
│       ├── valkey.py        # BGSAVE + RDB copy via Docker SDK
│       └── nats.py          # nats CLI for JetStream streams
├── tests/
├── milvus-backup.yaml       # Runtime config for milvus-backup tool
├── workspace.yaml           # Dagster workspace config (baked into Docker image)
├── entrypoint.sh            # Starts daemon + webserver
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## Operational Notes

### Dagster UI

Access at `http://localhost:3004` (dev/local). Features:

- **Asset graph**: Shows 6 backup assets in "backup" group with daily calendar view
- **Manual backup**: Click "Materialize" on asset, select date partition
- **Restore**: Jobs → `full_restore_job` → Launchpad → enter timestamp → Launch
- **Schedule**: Toggleable daily backup schedule in Schedules tab

### Milvus: collections not loaded after restore

After `milvus-backup restore`, collections are recreated with schemas and indexes but are **not loaded into memory**.
This is standard Milvus behavior — applications must call `load_collection()` on startup. All AI-Hub agents already do
this, so no manual intervention is needed in normal operation.

### Neo4j: brief downtime during backup

Neo4j Community Edition does not support online backups. The Neo4j container is stopped briefly (~10s) while
`neo4j-admin database dump` runs, then restarted automatically.

### Valkey: non-blocking BGSAVE

Valkey backup uses `BGSAVE` (non-blocking background save) via Docker exec. The container stays running during backup.
For restore, the container is briefly stopped to replace the RDB file, then restarted. Valkey persistence uses both RDB
snapshots and AOF for durability.

### NATS: JetStream per-stream backup

NATS JetStream streams are backed up individually using the official `nats` CLI installed in the backup container. The
CLI connects over the network. If no streams exist, an empty archive is created to satisfy restore validation.

## Pre-Commit

```bash
make pr-ready  # Format + lint
make test      # Run tests
```

## Local Development

```bash
cd aihub_backup
make dev       # Starts Dagster dev server (auto-reload)
```
