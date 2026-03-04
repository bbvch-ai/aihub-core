# aihub_backup - Centralized Backup & Restore Service

**Purpose**: Backup and restore orchestration for all AI-Hub data services. Runs as 3 Dagster containers (gRPC code
server + daemon + webserver) with no dependency on `aihub_lib`. Backs up PostgreSQL (x2), Milvus, Neo4j, ClickHouse,
Valkey, and NATS JetStream to S3 (SeaweedFS).

## Folder Structure

```
aihub_backup/
├── aihub_backup/
│   ├── settings.py              # Pydantic BaseSettings (env vars, no prefix)
│   ├── s3.py                    # boto3 S3 wrapper (SeaweedFS-compatible)
│   ├── docker_client.py         # Docker SDK wrapper (container ops)
│   ├── models.py                # Enums (ServiceStatus), result models, constants
│   ├── container_discovery.py   # Dynamic container discovery via compose project label
│   ├── container_lifecycle.py   # SERVICE_DEPS + ContainerLifecycleManager
│   ├── retention.py             # S3 retention cleanup (oldest backups past retention window)
│   ├── dagster/
│   │   ├── __init__.py          # defs = backup_definitions()
│   │   ├── definitions.py       # backup_definitions() factory — assembles all Dagster objects
│   │   ├── assets/
│   │   │   ├── handler_factory.py          # Shared handler construction (create_handler)
│   │   │   ├── backup_session_factory.py   # Root asset: init backup run, return BackupContext
│   │   │   ├── backup_service_factory.py   # Per-service asset factory (handler.backup())
│   │   │   ├── backup_finalize_factory.py  # Fan-in: restart services, run retention
│   │   │   ├── restore_session_factory.py  # Root asset: validate backup, stop services
│   │   │   ├── restore_service_factory.py  # Per-service asset factory (handler.restore())
│   │   │   └── restore_finalize_factory.py # Fan-in: restart services, report results
│   │   ├── ops/
│   │   │   └── types.py         # BackupContext, RestoreContext (Pydantic models)
│   │   ├── resources/
│   │   │   ├── BackupSettingsResource.py        # ConfigurableResource[BackupSettings]
│   │   │   ├── S3ManagerResource.py             # ConfigurableResource[S3Manager]
│   │   │   ├── DockerManagerResource.py         # ConfigurableResource[DockerManager]
│   │   │   ├── ContainerLifecycleResource.py    # ConfigurableResource[ContainerLifecycleManager]
│   │   │   ├── ContainerDiscoveryResource.py    # ConfigurableResource[ContainerDiscovery]
│   │   │   └── factory.py                       # backup_resources() → dict
│   │   ├── partitions.py        # DynamicPartitionsDefinition for restore timestamp selection
│   │   ├── jobs/
│   │   │   └── factory.py       # backup_asset_job, restore_asset_job
│   │   └── schedules/
│   │       └── factory.py       # daily_backup_schedule (2 AM Europe/Zurich)
│   └── services/
│       ├── base.py              # BackupHandler ABC
│       ├── postgres.py          # pg_dumpall/psql (subprocess, 2 hosts)
│       ├── milvus.py            # milvus-backup CLI (subprocess, integrity checks)
│       ├── neo4j.py             # neo4j-admin via Docker SDK (offline, temp container)
│       ├── clickhouse.py        # clickhouse-connect + Docker SDK
│       ├── valkey.py            # BGSAVE + RDB copy via Docker SDK
│       └── nats.py              # nats CLI for JetStream streams (subprocess)
├── tests/
├── milvus-backup.yaml           # Runtime config template for milvus-backup tool
├── workspace.yaml               # Dagster workspace config (points to backup-code gRPC server)
├── Dockerfile                   # Python 3.13, pg_client-17, milvus-backup, nats CLI
├── Makefile
└── pyproject.toml
```

## Architecture

**Dagster Layer**: 3-container deployment following Dagster best practices (same pattern as the pipeline stack):
`backup-code` (gRPC code server, executes runs, has Docker socket + all env vars), `backup-daemon` (schedule/sensor
management), `backup-webserver` (UI on port 3000, mapped to 3004 on host). All three share one Docker image and a
DAGSTER_HOME volume (SQLite run/schedule storage).

**Dagster patterns** (mirrors `aihub_pipeline`):

- `ConfigurableResource[T]` with `create_resource()` → auto-resolved via `ResourceParam[T]` in ops/assets
- `ResourceDependency[T]` for chained resource dependencies (e.g., S3ManagerResource depends on BackupSettings)
- Factory functions for assets, jobs, schedules (one factory per file in dedicated subdirectories)
- `backup_definitions()` in `definitions.py` assembles everything (mirrors pipeline's `default_definitions()`)
- One class per file for resources, empty `__init__.py` files (no re-exports)

**Backup asset graph**:

```
backup_session ──→ postgres_backup  ──┐
               ──→ milvus_backup   ──┤
               ──→ neo4j_backup    ──┤
               ──→ clickhouse_backup─┤──→ backup_finalize
               ──→ valkey_backup   ──┤
               ──→ nats_backup     ──┘
```

- `backup_session`: generates timestamp, purges stale prefix, discovers and stops all managed containers via
  `ContainerDiscovery`. Returns `BackupContext` (includes `previously_running` list).
- Per-service assets: start handler dependencies (via `SERVICE_DEPS`) → `handler.backup()` → stop dependencies. Catch
  errors → return `ServiceResult`. Never raise.
- `backup_finalize`: fan-in, restarts `previously_running` containers, runs retention, syncs dynamic partitions.
- `@failure_hook` on backup job restarts containers if `backup_session` itself fails after stopping them.
- **Failure semantics**: Fail loud but not fast. Individual service failures do not block other backups. All services
  are attempted, containers are always restarted, and the run fails at finalize if any service failed.

**Restore asset graph**:

```
restore_session ──→ postgres_restore  ──┐
                ──→ milvus_restore   ──┤
                ──→ neo4j_restore    ──┤
                ──→ clickhouse_restore─┤──→ restore_finalize
                ──→ valkey_restore   ──┤
                ──→ nats_restore     ──┘
```

- `restore_session`: resolves timestamp, validates backup completeness, stops all managed containers. Returns
  `RestoreContext(timestamp)`.
- Per-service assets: start handler dependencies → `handler.restore(timestamp)` → stop dependencies. Exceptions
  propagate (crash the asset). All run in parallel (same disjoint-deps guarantee as backup).
- `restore_finalize`: fan-in, restarts all managed containers. Only executes if every service asset succeeded (Dagster
  skips it when any upstream dependency fails).
- No `@failure_hook` on restore job — if any restore fails, containers stay stopped and a human must investigate.
- **Failure semantics**: Fail fast, loud, and catastrophically. A partially restored system is dangerous. If any service
  restore fails, the run crashes, containers remain stopped, and no automatic recovery is attempted. A human must act.

**Container Discovery** (`container_discovery.py`): Discovers all platform containers using the built-in Docker Compose
`com.docker.compose.project` label. No custom labels needed — Docker Compose adds this automatically. Excludes
infrastructure that must stay running: `backup-*`, `seaweedfs-*`, `etcd`. Adding or removing services from Docker
Compose requires **zero changes** to backup code.

**Container Lifecycle** (`container_lifecycle.py`): `SERVICE_DEPS` maps each handler to the containers it needs running
(or `None` for offline handlers like Neo4j). `ContainerLifecycleManager` provides `stop_containers()` and
`start_and_await_healthy()` utilities. An import-time disjointness assertion validates that no two handlers share a
container dependency (required for parallel backup and restore).

**Service Handlers**: Each implements `BackupHandler` ABC with `backup(backup_id, s3_prefix)` and
`restore(backup_prefix)`. Three implementation styles:

- **Subprocess-based**: PostgreSQL (`pg_dumpall`/`psql`), Milvus (`milvus-backup` CLI), NATS (`nats` CLI)
- **Python client + Docker SDK**: ClickHouse (`clickhouse-connect` for SQL, Docker for file copy), Valkey (`redis`
  client for BGSAVE/LASTSAVE, Docker for RDB file copy)
- **Docker SDK only**: Neo4j (temp sibling container with shared `/data` volume, main container stopped by
  orchestration)

**S3 Storage**: All backups stored in SeaweedFS under `s3://{bucket}/{timestamp}/`. Timestamp format:
`YYYY-MM-DD_HH-MM-SS`.

**Dynamic Partitions**: After each backup, `backup_finalize` syncs S3 prefixes to a `DynamicPartitionsDefinition`
(`backup_timestamps`). The `full_restore_job` uses this partition definition, so the Dagster UI shows a dropdown of
available backup timestamps when launching a restore.

## Key Design Decisions

**Synchronous I/O**: All handlers are synchronous. Dagster ops execute in a sync context, and all I/O is process-local
(Docker SDK, subprocess, boto3) where async would add complexity without benefit.

**No aihub_lib dependency**: Fully self-contained. Does not use shared infrastructure settings, NATS events, or
MongoEngine entities.

**Dynamic container discovery**: Uses `com.docker.compose.project` label (automatically set by Docker Compose) to
discover containers at runtime. No hardcoded container lists — adding/removing services in Docker Compose requires zero
changes to backup code.

**Parallel backup and restore with disjoint deps**: Per-service assets run in parallel (Dagster fan-out) for both backup
and restore. Each handler declares its container dependencies in `SERVICE_DEPS`. An import-time assertion enforces that
no two handlers share a container, preventing race conditions during parallel execution.

**Milvus collections not loaded after restore**: Standard Milvus behavior. Applications must call `load_collection()` on
startup. All AI-Hub agents already do this.

**Neo4j requires brief downtime**: Community Edition has no online backup. Container is stopped by the orchestration
layer, dump taken via temp sibling container with shared `/data` volume, then restarted.

**Hierarchical asset keys**: Assets use `AssetKey(["backup", "session"])` etc. Dagster converts these to op names with
double underscores (e.g., `backup__session`). RunConfig ops keys must use this double-underscore form.

## Adding a New Service

1. Create `services/{name}.py` implementing `BackupHandler` ABC (`service_name`, `backup`, `restore`)
2. Add service name to `BACKUP_SERVICES` tuple in `models.py`
3. Add `SERVICE_TO_ASSET_KEY` mapping in `models.py`
4. Add handler class to `HANDLER_FACTORIES` in `dagster/assets/handler_factory.py`
5. Add service key + factory call in `dagster/definitions.py` (both backup and restore sections)
6. Add `SERVICE_DEPS` entry in `container_lifecycle.py` (containers needed, timeout)
7. Add env vars in `deployment/templates/docker-compose.yml.j2` `backup-code` service block + `depends_on`
8. Add env var defaults in `.env.dev` and `.env.prod`

Compile-time assertions catch mismatches: `BACKUP_SERVICES` vs `SERVICE_DEPS` keys, and overlapping container deps
across handlers.

## Container Dependencies (SERVICE_DEPS)

```
SERVICE_DEPS: {service: (containers, timeout)}
  PostgreSQL: (["postgres", "postgres-ferretdb"], 60s)
  Neo4j:      (None, 0)     # offline: main container must be STOPPED
  ClickHouse: (["clickhouse"], 60s)
  Valkey:     (["valkey"], 60s)
  NATS:       (["nats"], 60s)
  Milvus:     (["milvus"], 180s)
```

Container discovery is automatic — no hardcoded container lists to maintain. Adding or renaming Docker Compose services
requires zero changes to backup code.

## Testing

- pytest with `e2e` marker excluded by default. Run with `make test`.
- Mocking: `unittest.mock.MagicMock` for S3Manager, DockerManager, Docker SDK, subprocess
- Subprocess mocks: patch `subprocess.Popen`/`subprocess.run`, use `BytesIO` for stdout/stderr
- Docker mocks: patch `docker.from_env()`, mock container lifecycle calls
- Python client mocks: patch `_create_client` on ClickHouse/Valkey handlers, mock `clickhouse-connect`/`redis` clients
- Dagster resources: patch class constructors on resource modules (e.g.,
  `@patch("aihub_backup.dagster.resources.BackupSettingsResource.BackupSettings")`) since `ConfigurableResource` uses
  frozen pydantic models
- Handler fixtures are per-test-module (e.g., `postgres_handler` in `test_postgres.py`)

## Commands

```bash
make test        # Run pytest
make pr-ready    # Format + lint + typecheck (ruff + mypy)
make dev         # Start Dagster dev server (auto-reload)
```

## Dagster UI

Access at `http://localhost:3004`. Key operations:

- **Manual backup**: Assets → Materialize all
- **Restore**: Jobs → `full_restore_job` → select partition (backup timestamp) → Launch
- **Schedule**: Schedules tab → toggle `daily_backup_schedule` (2 AM Europe/Zurich)
