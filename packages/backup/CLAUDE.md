# packages/backup - Centralized Backup & Restore Service

**Purpose**: Backup and restore orchestration for all stateful AI-Hub services. Independent Dagster instance (3
containers: gRPC code server, daemon, webserver) with SQLite storage. Backs up PostgreSQL (x2), Milvus, Neo4j,
ClickHouse, Valkey, and NATS JetStream to S3 (SeaweedFS).

## Folder Structure

```
packages/backup/swiss_ai_hub/backup/
├── settings.py              # Pydantic BaseSettings (env vars)
├── s3.py                    # boto3 S3 wrapper (SeaweedFS-compatible)
├── docker_client.py         # Docker SDK wrapper (container ops)
├── models.py                # Enums (ServiceStatus), result models, constants
├── container_discovery.py   # Dynamic container discovery via compose project label
├── container_lifecycle.py   # SERVICE_DEPS + ContainerLifecycleManager
├── retention.py             # S3 retention cleanup (oldest backups past retention window)
├── dagster/
│   ├── definitions.py       # backup_definitions() — assembles all Dagster objects
│   ├── types.py             # BackupContext, RestoreContext (Pydantic models)
│   ├── partitions.py        # DynamicPartitionsDefinition for restore timestamp selection
│   ├── assets/
│   │   ├── handler_factory.py          # HANDLER_FACTORIES dict + create_handler()
│   │   ├── backup_session_factory.py   # Root: init backup, stop containers
│   │   ├── backup_service_factory.py   # Per-service: handler.backup()
│   │   ├── backup_finalize_factory.py  # Fan-in: restart, retention, sync partitions
│   │   ├── restore_session_factory.py  # Root: validate backup, stop containers
│   │   ├── restore_service_factory.py  # Per-service: handler.restore()
│   │   └── restore_finalize_factory.py # Fan-in: restart, report results
│   ├── resources/           # Dagster ConfigurableResource wrappers (snake_case files)
│   ├── jobs/factory.py      # backup_asset_job, restore_asset_job, restart_on_failure hook
│   └── schedules/factory.py # daily_backup_schedule (1 AM Europe/Zurich)
└── services/
    ├── base.py              # BackupHandler ABC (backup + restore methods)
    ├── postgres.py          # pg_dumpall/pg_dump + DocumentDB catalog COPY workaround
    ├── milvus.py            # milvus-backup CLI (subprocess)
    ├── neo4j.py             # neo4j-admin via temp sibling container
    ├── clickhouse.py        # BACKUP/RESTORE TO Disk('backup_s3', ...) SQL
    ├── valkey.py            # BGSAVE + RDB copy, AOF reconstruction on restore
    └── nats.py              # nats CLI stream backup/restore
```

## Key Patterns

- **Asset graph**: session → 6 per-service assets → finalize (same structure for backup and restore)
- **PostgreSQL**: `PostgresHandler` backs up both `postgres` and `postgres-ferretdb` in a single asset
- **Container lifecycle**: All managed containers stopped before backup, restarted after. Excluded prefixes: `backup-`,
  `seaweedfs-`, `etcd`, `traefik`
- **Parallel ops**: `ThreadPoolExecutor` for container stop/start
- **Failure safety**: `restart_on_failure` hook restarts all containers if backup crashes mid-run
- **Sync by design**: All handlers are synchronous. Dagster ops execute in a sync context, and all I/O is process-local
  (Docker SDK, subprocess, boto3). Do not convert to async — this overrides the root-level "async consistently" rule
- **Adding a new handler**: Implement `BackupHandler` ABC in `services/`. If the handler needs Docker access, type-hint
  a `DockerManager` parameter in `__init__` — `create_handler()` introspects the signature to decide whether to inject
  it. Register the handler in `HANDLER_FACTORIES` in `handler_factory.py`

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

- Unit tests mock Docker, S3, and subprocess calls — no infrastructure needed
- E2E tests (`test_e2e.py`, marker `e2e`) run a full backup/restore cycle against the dev stack
- `conftest.py` provides shared fixtures for `BackupSettings` and handler construction
