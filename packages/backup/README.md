<div align="center">

# swiss-ai-hub-backup

**The centralized backup, restore, and PostgreSQL-maintenance service for
[Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) — a self-contained [Dagster](https://dagster.io/) instance that
snapshots every stateful service to S3.**

[![PyPI](https://img.shields.io/pypi/v/swiss-ai-hub-backup?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/swiss-ai-hub-backup/)
[![Python](https://img.shields.io/pypi/pyversions/swiss-ai-hub-backup?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/swiss-ai-hub-backup/)
[![License](https://img.shields.io/badge/license-AGPL%203.0--or--later-blue?style=flat-square)](https://github.com/bbvch-ai/aihub-core/blob/main/packages/backup/LICENSE)

</div>

______________________________________________________________________

## What is Swiss AI Hub?

[Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) is an open-source, self-hosted AI platform for enterprises. One
`docker compose up` starts ~30 integrated containers across several stateful stores — PostgreSQL, FerretDB, Milvus,
Neo4j, ClickHouse, Valkey, and NATS JetStream. **This package keeps that data safe.**

## What is this package?

`swiss-ai-hub-backup` is the platform's **backup/restore and database-maintenance plane**. It runs as its own
independent [Dagster](https://dagster.io/) instance (separate from the data pipelines, with its own SQLite storage) and:

- **Backs up** PostgreSQL (×2), Milvus, Neo4j, ClickHouse, Valkey, and NATS JetStream to S3 (SeaweedFS) on a schedule —
  gracefully stopping and restarting the managed containers around each run for consistent snapshots.
- **Restores** any service from a chosen backup timestamp.
- **Maintains** the platform PostgreSQL online: prunes verbose Dagster `event_logs`, tunes autovacuum, and runs
  `pg_repack` — so deployments stay bounded over time without downtime.

Each stateful service has a `BackupHandler` (`postgres`, `milvus`, `neo4j`, `clickhouse`, `valkey`, `nats`); the whole
thing is wired into a Dagster asset graph by `backup_definitions()`. Because it operates on the storage layer and needs
to stop containers, it requires **read access to the Docker socket** (`/var/run/docker.sock`), which it uses to discover
platform containers via their `com.docker.compose.project` label.

> Unlike the other Swiss AI Hub packages, this is an **operational service**, not a library you build agents/APIs on. It
> is licensed **AGPL-3.0-or-later** (the rest of the SDK is Apache-2.0).

## Should you use this package?

**Most operators don't install it directly — it ships with the platform** as the `backup-*` containers (a gRPC code
server, a daemon, and a webserver UI on `:3004`). You'd reach for this PyPI package to **run the backup plane
standalone, embed its logic, or extend it** — for example, adding a `BackupHandler` for a stateful service of your own.

## What it does

| Job                                      | Schedule  | Stops containers?          |
| ---------------------------------------- | --------- | -------------------------- |
| Full backup (all services → S3)          | daily     | Yes (consistent snapshots) |
| Restore (service ← chosen timestamp)     | on demand | Yes                        |
| `event_logs` cleanup + autovacuum tuning | weekly    | No (online-safe)           |
| `pg_repack` (reclaim disk)               | monthly   | No (online-safe)           |

## Installation

```bash
pip install swiss-ai-hub-backup
# or
uv add swiss-ai-hub-backup
```

Requires **Python 3.13**.

______________________________________________________________________

## Quick start

The backup plane is a Dagster code location built by `backup_definitions()`:

```python
# my_backup/__init__.py
from swiss_ai_hub.backup.dagster.definitions import backup_definitions

defs = backup_definitions()   # 26 assets, 4 jobs: backup, restore, cleanup, repack
```

Inspect and run it with the Dagster UI (it keeps its own state in `DAGSTER_HOME`):

```bash
export DAGSTER_HOME=/tmp/backup-dagster && mkdir -p "$DAGSTER_HOME"
set -a && source .env && set +a          # S3 + DB credentials, BACKUP_* settings
dagster dev -m my_backup                 # http://localhost:3000
```

From the UI you can materialize the **online-safe maintenance jobs** (cleanup, `pg_repack`) against a running stack
without disruption. The **full backup/restore jobs stop and restart containers**, so run those deliberately — and note
they need access to the Docker socket and to all the stateful services. `dagster definitions validate -m my_backup`
loads the whole code location without running anything (a fast CI/sanity check).

> **Settings are not auto-loaded from the environment.** Connection and `BACKUP_*` settings are read only when
> constructed, so export them in the process that runs Dagster (`set -a && source .env && set +a`).

______________________________________________________________________

## How it's deployed

In production the backup plane runs as **three containers from one image**, forming a self-contained Dagster instance:

| Container          | Role                                                      | Notes                                                                            |
| ------------------ | --------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `backup-code`      | Dagster gRPC **code server** (`dagster api grpc … :4266`) | mounts `/var/run/docker.sock:ro` to stop/start containers; on `data` + `storage` |
| `backup-daemon`    | Dagster **daemon**                                        | runs the schedules and sensors; on `data`                                        |
| `backup-webserver` | Dagster **UI** (`:3004`)                                  | inspect runs, trigger restores; on `proxy` + `data`                              |

Because it needs the Docker socket and the platform's stateful services, the canonical deployment is the platform's own
backup compose. See [`infra/deployment`](https://github.com/bbvch-ai/aihub-core/tree/main/infra/deployment) and the
[documentation](https://bbvch-ai.github.io/aihub-core/) for the full container setup, retention config, and the
`BACKUP_*` environment variables. If you run your own variant, mirror that three-container shape and grant the code
server read access to the Docker socket.

## Extending — add a service to back up

Implement the `BackupHandler` ABC for your service in `services/`, then register it in `HANDLER_FACTORIES` — the Dagster
asset wiring picks it up automatically (handlers are synchronous by design):

```python
from swiss_ai_hub.backup.services.base import BackupHandler

class MyServiceHandler(BackupHandler):
    def backup(self, context) -> ...:
        ...   # dump your service's state to S3
    def restore(self, context) -> ...:
        ...   # restore it from a backup
```

If the handler needs Docker access, type-hint a `DockerManager` parameter in `__init__` and the factory injects it. The
maintenance subsystem follows the same pattern (`MaintenanceHandler` + `CLEANUP_HANDLER_NAMES`). See the
[documentation](https://bbvch-ai.github.io/aihub-core/) for the full handler contract.

______________________________________________________________________

## Links

- **Source & issues**: https://github.com/bbvch-ai/aihub-core
- **Documentation**: https://bbvch-ai.github.io/aihub-core/

## License

**AGPL-3.0-or-later** — see
[packages/backup/LICENSE](https://github.com/bbvch-ai/aihub-core/blob/main/packages/backup/LICENSE). Note this differs
from the Apache-2.0 SDK packages; for the full per-package license matrix, see
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).

______________________________________________________________________

<div align="center">

Part of [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core). Built in Switzerland by
[bbv Software Services](https://www.bbv.ch).

</div>
