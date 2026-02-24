# aihub_backup - Centralized Backup & Restore Service

**Purpose**: Backup and restore orchestration for all AI-Hub data services. Runs as a standalone Dagster container
(webserver + daemon) with no dependency on `aihub_lib`. Backs up PostgreSQL (x2), Milvus, Neo4j, ClickHouse, Valkey, and
NATS JetStream to S3 (SeaweedFS).

## Folder Structure

```
aihub_backup/
├── aihub_backup/
│   ├── settings.py          # Pydantic BaseSettings (env vars, no prefix)
│   ├── s3.py                # boto3 S3 wrapper (SeaweedFS-compatible)
│   ├── docker_client.py     # Docker SDK wrapper (container lifecycle)
│   ├── models.py            # Enums (BackupMode, ServiceStatus), result models, constants
│   ├── orchestrator.py      # Backup/restore coordination across all services
│   ├── retention.py         # S3 retention cleanup (offline backups never deleted)
│   ├── dagster/
│   │   ├── __init__.py      # Dagster Definitions (code location entry point)
│   │   ├── config.py        # BackupConfig, RestoreConfig, SingleServiceRestoreConfig
│   │   ├── resources.py     # ConfigurableResource wrappers for Dagster DI
│   │   ├── assets.py        # @multi_asset create_backup (daily partitioned, 6 outputs)
│   │   ├── jobs.py          # backup_asset_job, full_restore_job, single_service_restore_job
│   │   ├── schedules.py     # daily_backup_schedule (2 AM Europe/Zurich)
│   │   └── ops/
│   │       └── restore_ops.py  # run_full_restore, run_single_service_restore
│   └── services/
│       ├── base.py          # BackupHandler ABC
│       ├── postgres.py      # pg_dumpall/psql (subprocess, 2 hosts)
│       ├── milvus.py        # milvus-backup CLI (subprocess, integrity checks)
│       ├── neo4j.py         # neo4j-admin via Docker SDK (offline, temp container)
│       ├── clickhouse.py    # clickhouse-connect + Docker SDK
│       ├── valkey.py        # BGSAVE + RDB copy via Docker SDK
│       └── nats.py          # nats CLI for JetStream streams (subprocess)
├── tests/
├── milvus-backup.yaml       # Runtime config template for milvus-backup tool
├── workspace.yaml           # Dagster workspace config (baked into Docker image)
├── entrypoint.sh            # Starts daemon + webserver, signal handling
├── Dockerfile               # Python 3.13, pg_client-17, milvus-backup, nats CLI
├── Makefile
└── pyproject.toml
```

## Architecture

**Dagster Layer**: Thin wrapper around the core orchestrator. Resources create instances, assets/ops call orchestrator
methods, MaterializeResult captures per-service metadata. The Dagster webserver (port 3000, mapped to 3004 on host)
provides monitoring, manual triggers, and parameterized restores via Launchpad.

**Orchestrator**: Coordinates backup/restore across all services. Handles container lifecycle for restore (4-phase:
validate → stop all → restore data → start all). Container stop/start order is dependency-aware (apps → infra →
databases down, databases → infra → apps up).

**Service Handlers**: Each implements `BackupHandler` ABC with `backup(timestamp, prefix)` and `restore(timestamp)`. Two
implementation styles:

- **Subprocess-based**: PostgreSQL (`pg_dumpall`/`psql`), Milvus (`milvus-backup` CLI), NATS (`nats` CLI)
- **Docker SDK-based**: Neo4j (temp container with shared volume), ClickHouse, Valkey (BGSAVE + RDB copy)

**S3 Storage**: All backups stored in SeaweedFS under `s3://{bucket}/{timestamp}_{mode}/`. Timestamp format:
`YYYY-MM-DD_HH-MM-SS`. Mode: `online` or `offline`.

## Key Design Decisions

**Synchronous I/O**: All handlers are synchronous. Dagster ops execute in a sync context, and all I/O is process-local
(Docker SDK, subprocess, boto3) where async would add complexity without benefit.

**No aihub_lib dependency**: Fully self-contained. Does not use shared infrastructure settings, NATS events, or
MongoEngine entities.

**Offline backups never deleted**: Retention cleanup only removes online backups past the retention window. Offline
backups (which require stopping app containers) are preserved indefinitely.

**Offline preferred over online**: When both modes exist for the same timestamp, `resolve_timestamp` and
`find_latest_backup` prefer offline (more consistent).

**Milvus collections not loaded after restore**: Standard Milvus behavior. Applications must call `load_collection()` on
startup. All AI-Hub agents already do this.

**Neo4j requires brief downtime**: Community Edition has no online backup. Container is stopped, dump taken via temp
sibling container with shared `/data` volume, then restarted.

## Adding a New Service

1. Create `services/{name}.py` implementing `BackupHandler` ABC (`service_name`, `backup`, `restore`)
2. Add service name to `BACKUP_SERVICES` tuple in `models.py`
3. Add `SERVICE_TO_ASSET_KEY` mapping in `models.py`
4. Add `AssetOut` entry in `assets.py` `create_backup` `outs` dict
5. Instantiate handler in `resources.py` `BackupHandlersResource.create_handlers()`
6. Add `RESTORE_STEPS` entry in `orchestrator.py` (start_before, stop_after, start_timeout)
7. Add validation check in `orchestrator.py` `_validate_backups()`

Compile-time assertions in `models.py`, `config.py`, and `resources.py` will catch mismatches.

## Container Lifecycle (Restore)

```
RESTORE_STEPS: {service: (start_before, stop_after, start_timeout)}
  PostgreSQL: (["postgres", "postgres-ferretdb"], same, 60s)
  Neo4j:      (None, None, 0)     # handled internally by handler
  ClickHouse: (["clickhouse"], same, 60s)
  Valkey:     (None, None, 0)     # handled internally by handler
  NATS:       (["nats"], same, 60s)
  Milvus:     (["milvus"], same, 180s)
```

If you add, remove, or rename a Docker Compose service, update `APP_CONTAINERS`, `INFRA_CONSUMERS`,
`DATABASE_CONTAINERS`, `START_ORDER_INFRA`, `START_ORDER_SERVICES`, and `START_ORDER_APPS` in `orchestrator.py`. Runtime
assertions verify these stay in sync.

## Testing

- pytest, no markers. Run with `make test`.
- Mocking: `unittest.mock.MagicMock` for S3Manager, DockerManager, Docker SDK, subprocess
- Subprocess mocks: patch `subprocess.Popen`/`subprocess.run`, use `BytesIO` for stdout/stderr
- Docker mocks: patch `docker.from_env()`, mock container lifecycle calls
- Dagster resources: `conftest.py` provides `settings` and `dagster_resources` fixtures
- Handler fixtures are per-test-module (e.g., `postgres_handler` in `test_postgres.py`)

## Commands

```bash
make test        # Run pytest
make pr-ready    # Format + lint + typecheck (ruff + mypy)
make dev         # Start Dagster dev server (auto-reload)
```

## Dagster UI

Access at `http://localhost:3004`. Key operations:

- **Manual backup**: Assets → Materialize → select date partition
- **Restore**: Jobs → `full_restore_job` or `single_service_restore_job` → Launchpad → enter config → Launch
- **Schedule**: Schedules tab → toggle `daily_backup_schedule` (2 AM Zurich, online mode)
