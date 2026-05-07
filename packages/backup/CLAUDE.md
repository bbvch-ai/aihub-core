# packages/backup - Centralized Backup, Restore & Postgres Maintenance Service

**Purpose**: Backup and restore orchestration for all stateful AI-Hub services PLUS continuous Postgres health
maintenance for the dagster DB. Independent Dagster instance (3 containers: gRPC code server, daemon, webserver) with
SQLite storage. Backs up PostgreSQL (x2), Milvus, Neo4j, ClickHouse, Valkey, and NATS JetStream to S3 (SeaweedFS).
Prunes verbose `event_logs` rows weekly and runs `pg_repack` monthly to keep the platform Postgres bounded over time.

## Folder Structure

```
packages/backup/swiss_ai_hub/backup/
├── settings.py              # Pydantic BaseSettings (env vars) — backup AND maintenance config
├── s3.py                    # boto3 S3 wrapper (SeaweedFS-compatible)
├── docker_client.py         # Docker SDK wrapper (container ops)
├── models.py                # Enums (ServiceStatus), result models, constants
├── container_discovery.py   # Dynamic container discovery via compose project label
├── container_lifecycle.py   # SERVICE_DEPS + ContainerLifecycleManager
├── retention.py             # S3 retention cleanup (oldest backups past retention window)
├── dagster/
│   ├── definitions.py       # backup_definitions() — assembles backup + maintenance Dagster objects
│   ├── types.py             # BackupContext, RestoreContext, MaintenanceContext
│   ├── partitions.py        # DynamicPartitionsDefinition for restore timestamp selection
│   ├── assets/
│   │   ├── handler_factory.py              # Backup HANDLER_FACTORIES dict + create_handler()
│   │   ├── backup_session_factory.py       # Root: init backup, stop containers
│   │   ├── backup_service_factory.py       # Per-service: handler.backup()
│   │   ├── backup_finalize_factory.py      # Fan-in: restart, retention, sync partitions
│   │   ├── restore_session_factory.py      # Root: validate backup, stop containers
│   │   ├── restore_service_factory.py      # Per-service: handler.restore()
│   │   ├── restore_finalize_factory.py     # Fan-in: restart, report results
│   │   ├── maintenance_handler_factory.py  # CLEANUP_HANDLER_NAMES + create_maintenance_handler
│   │   ├── maintenance_session_factory.py  # Root: timestamp + run_id (NO container stop)
│   │   ├── maintenance_service_factory.py  # Per-handler: handler.run() — failures isolated
│   │   └── maintenance_finalize_factory.py # Fan-in: aggregate results
│   ├── resources/           # Dagster ConfigurableResource wrappers (incl. MaintenanceEngineResource)
│   ├── jobs/factory.py      # backup_asset_job, restore_asset_job, cleanup_asset_job, repack_asset_job
│   └── schedules/factory.py # daily_backup, weekly_cleanup, monthly_repack (all Europe/Zurich)
├── services/                 # Backup handlers (one per stateful service)
│   ├── base.py               # BackupHandler ABC (backup + restore methods)
│   ├── postgres.py           # pg_dumpall/pg_dump + DocumentDB catalog COPY workaround
│   ├── milvus.py             # milvus-backup CLI (subprocess)
│   ├── neo4j.py              # neo4j-admin via temp sibling container
│   ├── clickhouse.py         # BACKUP/RESTORE TO Disk('backup_s3', ...) SQL
│   ├── valkey.py             # BGSAVE + RDB copy, AOF reconstruction on restore
│   └── nats.py               # nats CLI stream backup/restore
└── maintenance/              # Postgres maintenance handlers (run() returns MaintenanceResult)
    ├── base.py                       # MaintenanceHandler ABC, MaintenanceResult
    ├── postgres_engine.py            # SQLAlchemy Engine factory (NullPool, direct postgres connect)
    ├── dagster_cleanup_sql.py        # Shared CTE-based DELETE with LIMIT (caps WAL spike)
    ├── dagster_debug_logs.py         # DELETE level=10 user logs older than retention
    ├── dagster_info_logs.py          # DELETE level=20 user logs older than retention
    ├── dagster_warning_logs.py       # DELETE level=30 user logs older than retention
    ├── dagster_unimportant_events.py # DELETE ENGINE_EVENT/HANDLED_OUTPUT/LOADED_INPUT/MAT_PLANNED/STEP_OUTPUT
    ├── postgres_indexes.py           # CREATE INDEX CONCURRENTLY IF NOT EXISTS — idempotent
    ├── postgres_autovacuum_tune.py   # ALTER TABLE SET autovacuum_vacuum_scale_factor — idempotent
    └── postgres_repack.py            # subprocess pg_repack -t event_logs/runs/job_ticks
```

## Key Patterns

- **Asset graph**: session → 6 per-service assets → finalize (same structure for backup and restore)
- **PostgreSQL**: `PostgresHandler` backs up both `postgres` and `postgres-ferretdb` in a single asset
- **Container lifecycle**: All managed containers stopped before backup, restarted after. Excluded prefixes: `backup-`,
  `seaweedfs-`, `etcd`, `traefik`, `oauth2proxy` (Traefik + all oauth2proxy sidecars stay up so the backup Dagster UI
  remains reachable through OAuth during a backup run; note Keycloak still goes down with `postgres`, so existing
  sessions work but token refresh will fail mid-run)
- **Parallel ops**: `ThreadPoolExecutor` for container stop/start
- **Failure safety**: `restart_on_failure` hook restarts all containers if backup crashes mid-run
- **Sync by design**: All handlers are synchronous. Dagster ops execute in a sync context, and all I/O is process-local
  (Docker SDK, subprocess, boto3). Do not convert to async — this overrides the root-level "async consistently" rule
- **Postgres subprocess timeout**: `POSTGRES_SUBPROCESS_TIMEOUT_SECONDS` (default 6h) caps every `pg_dump` /
  `pg_restore` / `psql` invocation. Sized for >100GB dagster DBs; lower for small deployments
- **NATS readiness**: `NatsHandler._wait_for_ready` probes `stream list` (not `rtt`) so it actually checks JetStream,
  and `_run_nats_subprocess` retries up to 3× on transient connect errors ("no servers available", "connection
  refused/reset") with a re-probe between attempts. Non-transient errors (e.g. stream-not-found) surface immediately
- **Adding a new handler**: Implement `BackupHandler` ABC in `services/`. If the handler needs Docker access, type-hint
  a `DockerManager` parameter in `__init__` — `create_handler()` introspects the signature to decide whether to inject
  it. Register the handler in `HANDLER_FACTORIES` in `handler_factory.py`

## Maintenance Subsystem (Postgres Health)

The maintenance subsystem keeps the platform Postgres bounded over time so deployments don't accumulate `event_logs`
indefinitely. It lives **inside the backup Dagster instance** because backup is already the platform's "operate on the
storage layer" plane. Three jobs share one `maintenance_session` asset:

| Job                           | Schedule                   | Purpose                                                                                                           | Stops containers? |
| ----------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------- |
| `dagster_cleanup_job`         | Sundays 3 AM               | Prune verbose Python logs + transient framework events from `event_logs`; ensure cleanup indexes; tune autovacuum | No (online-safe)  |
| `postgres_repack_job`         | First Sunday of month 4 AM | `pg_repack` on `event_logs`, `runs`, `job_ticks` to return disk to OS                                             | No (online-safe)  |
| `daily_backup_job` (existing) | Daily 1 AM                 | Full backup with container stop/restart                                                                           | Yes               |

**UI safety guarantees** (these are load-bearing — do not change without re-reviewing the docs):

- `ASSET_MATERIALIZATION` events are NEVER deleted — the asset graph "last materialized" timestamp depends on them.
- `STEP_SUCCESS` / `STEP_FAILURE` events are NEVER deleted — the run detail page depends on them.
- `runs` table rows are NEVER deleted — the Runs tab depends on them. (Pruning runs is a separate, opt-in operation that
  is NOT part of the continuous maintenance.)
- `job_state` (sensor cursors, schedule state) is NEVER touched — would corrupt sensor/schedule operation.

**Adding a new maintenance handler**:

1. Subclass `MaintenanceHandler` in `maintenance/`. Implement `service_name` and `run() -> MaintenanceResult`.
2. Add the name to `CLEANUP_HANDLER_NAMES` (or `REPACK_HANDLER_NAMES`) in `maintenance_handler_factory.py` and add the
   construction branch in `create_maintenance_handler()`.
3. The Dagster asset wiring is automatic — `backup_definitions()` iterates `*_HANDLER_NAMES` to build assets.

**Configuration** (env vars on the `BackupSettings` class):

| Setting                                        | Default   | Purpose                                                             |
| ---------------------------------------------- | --------- | ------------------------------------------------------------------- |
| `MAINTENANCE_DEBUG_LOG_RETENTION_DAYS`         | 7         | Keep DEBUG logs (level=10) for N days                               |
| `MAINTENANCE_INFO_LOG_RETENTION_DAYS`          | 60        | Keep INFO logs (level=20) for N days                                |
| `MAINTENANCE_WARNING_LOG_RETENTION_DAYS`       | 60        | Keep WARNING logs (level=30) for N days                             |
| `MAINTENANCE_UNIMPORTANT_EVENT_RETENTION_DAYS` | 30        | Keep transient framework events for N days                          |
| `MAINTENANCE_BATCH_LIMIT`                      | 1_000_000 | Cap rows per DELETE — protects against WAL spikes on backlogged DBs |
| `MAINTENANCE_DISABLED`                         | false     | Kill switch — schedule becomes a no-op                              |
| `MAINTENANCE_POSTGRES_HOST`                    | postgres  | Connect directly (not pgbouncer) for stable session-mode            |
| `MAINTENANCE_POSTGRES_PORT`                    | 5432      |                                                                     |
| `MAINTENANCE_DAGSTER_DB`                       | dagster   | DB name to maintain                                                 |

**Failure isolation**: Each handler returns a `MaintenanceResult` rather than raising. The finalize asset aggregates and
only fails the run if ANY handler reported `succeeded=False`. One failed cleanup never blocks the others.

**`pg_repack` graceful degradation**: If the `pg_repack` binary or extension is missing (e.g., Postgres image hasn't
been updated yet), `PostgresRepackHandler.run()` returns `succeeded=True` with `metadata={"skipped": ...}` rather than
failing. Operators can install `pg_repack` later and the next monthly run picks it up.

**Reference**: docs.dagster.io/deployment/troubleshooting/database-tuning is the canonical recipe this subsystem
implements. The cleanup SQL targets exactly the event types the docs recommend; the indexes match exactly.

## DocumentDB Catalog Maintenance

`_DOCUMENTDB_CATALOG_TABLES` and `_DOCUMENTDB_CATALOG_SEQUENCES` in `services/postgres.py` are hardcoded. After
upgrading the DocumentDB extension, verify completeness against the `postgres` database on `postgres-ferretdb`:

```sql
SELECT c.relname, c.relkind FROM pg_class c
JOIN pg_depend d ON c.oid = d.objid
JOIN pg_extension e ON d.refobjid = e.oid
WHERE e.extname = 'documentdb' AND c.relkind IN ('r', 'S')
ORDER BY c.relkind, c.relname;
```

## Commands

| Command                          | What it does                           |
| -------------------------------- | -------------------------------------- |
| `make test`                      | Run unit tests (excludes e2e)          |
| `make typecheck`                 | Run type checker (`ty check`)          |
| `pytest -m e2e -v --timeout=600` | Run E2E tests (needs Docker dev stack) |

## Testing

Three layers, mirroring the test pyramid:

- **Layer 1 — Unit tests** (`tests/unit/`, marker `unit`): hermetic. Docker, S3, subprocess, and SQLAlchemy are mocked.
  No infrastructure needed.

- **Layer 2 — SQL contract tests** (`tests/integration/`, marker `integration`): exercise handlers that talk to Postgres
  against a real Postgres with a minimal seeded schema. Verifies semantic contracts the unit tests cannot (preserving
  load-bearing rows, idempotency, real-`jsonb` behavior). Skips automatically when no Postgres is reachable.

  Run via either:

  - `apt install postgresql` then `uv run pytest tests/integration/`
  - `docker run --rm -d --name pg-test -e POSTGRES_PASSWORD=test -p 55432:5432 postgres:17` then
    `PYTEST_POSTGRES_HOST=localhost PYTEST_POSTGRES_PORT=55432 PYTEST_POSTGRES_USER=postgres PYTEST_POSTGRES_PASSWORD=test uv run pytest tests/integration/`

- **Layer 3 — E2E tests** (`tests/integration/test_e2e.py`, marker `e2e`): full backup/restore cycle against the running
  dev stack. Requires `make up`. Slow.

`conftest.py` provides shared fixtures for `BackupSettings` and handler construction. The integration conftest
auto-detects `pg_ctl` (process mode) or external Postgres (noproc mode); both paths feed the same `event_logs_engine`
and `seed_events` fixtures.
