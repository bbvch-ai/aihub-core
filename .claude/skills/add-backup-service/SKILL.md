---
name: add-backup-service
description: >-
  Step-by-step guide for adding a new stateful service to the centralized backup system (aihub_backup).
  Covers all registration points: handler implementation, model constants, Dagster assets, container
  dependencies, settings, compose env vars, and .env files. Use when user says 'add backup for', 'backup new
  service', 'integrate into backup', 'new backup handler', or 'extend backup coverage'. Includes a
  validation script that checks all registration points. Do NOT use for debugging backup failures (use
  debug-pipeline skill) or reviewing backup coverage drift (use backup-coverage-checker agent).
---

# Add Backup Service

Add a new stateful service to the centralized backup system. This involves registration points across several files.
Compile-time assertions catch most internal mismatches, but compose/env wiring must be verified manually.

## Prerequisites

Before starting, confirm:

1. The service is stateful (persists data that would be lost if the container is recreated)
2. The service runs as a Docker container in `deployment/templates/docker-compose.yml.j2`
3. The service is NOT already in `aihub_backup/aihub_backup/models.py` `BACKUP_SERVICES`

Read `aihub_backup/CLAUDE.md` for architecture context.

## Step 1: Create the Handler

Create `aihub_backup/aihub_backup/services/{name}.py` implementing the `BackupHandler` ABC.

```python
from aihub_backup.services.base import BackupHandler
```

The ABC requires:

- `service_name` property returning the display name (must match `BACKUP_SERVICES` entry)
- `backup(backup_id: str, s3_prefix: str)` method
- `restore(backup_prefix: str)` method

**Choose an implementation style based on the service:**

| Style                      | When to use                                             | Exemplar                                           |
| -------------------------- | ------------------------------------------------------- | -------------------------------------------------- |
| Subprocess                 | Service has a CLI backup tool (pg_dump, nats backup)    | `aihub_backup/aihub_backup/services/nats.py`       |
| Python client              | Service has a Python client with native backup support  | `aihub_backup/aihub_backup/services/clickhouse.py` |
| Python client + Docker SDK | Service has a Python client AND needs container file IO | `aihub_backup/aihub_backup/services/valkey.py`     |
| Docker SDK only            | Backup requires temp containers or volume access        | `aihub_backup/aihub_backup/services/neo4j.py`      |

**Key patterns from exemplars:**

- Use `tempfile.mkdtemp(prefix="backup-{name}-")` for temp dirs, clean up in `finally`
- Upload to S3 at `{s3_prefix}/{filename}` via `self._s3.upload_file()`
- Download from S3 at `{backup_prefix}/{filename}` via `self._s3.download_file()`
- All handlers are synchronous (Dagster executes in sync context)
- Constructor takes `BackupSettings`, `S3Manager`, and optionally `DockerManager`
- Handlers do NOT manage container lifecycle — the orchestration layer handles stop/start

## Step 2: Register in models.py

Edit `aihub_backup/aihub_backup/models.py`:

1. Add the service display name to `BACKUP_SERVICES` tuple
2. Add mapping to `SERVICE_TO_ASSET_KEY` dict (format: `{name}_backup`)

The compile-time assertion at the bottom will catch any mismatch between these two.

## Step 3: Add Handler Factory

Edit `aihub_backup/aihub_backup/dagster/assets/handler_factory.py`:

1. Import the new handler class
2. Add entry to `HANDLER_FACTORIES` dict:

```python
"{Name}": NewHandler,
```

The `create_handler()` function uses `inspect.signature` to detect whether the handler constructor accepts a `docker`
parameter and passes `DockerManager` automatically — no manual wiring needed.

## Step 4: Add Dagster Asset + Key

Edit `aihub_backup/aihub_backup/dagster/definitions.py`:

1. Add asset key to the `service_keys` dict (backup):

```python
"{Name}": AssetKey(["backup", "{name}"]),
```

2. Add asset key to the `restore_service_keys` dict (restore):

```python
"{Name}": AssetKey(["restore", "{name}"]),
```

The factory call loops automatically create both backup and restore assets from these entries.

## Step 5: Add Container Dependencies

Edit `aihub_backup/aihub_backup/container_lifecycle.py`:

Add entry to `SERVICE_DEPS` dict:

```python
"{Name}": ServiceDeps(("container-name",), 60),
```

- `containers=None` if the handler needs the container STOPPED (like Neo4j offline dump)
- `containers=("container-name",)` if the handler needs the container RUNNING
- `timeout` is the health check wait time in seconds

**Important**: The import-time disjointness assertion will fail if the new handler's containers overlap with any
existing handler. Each handler must have exclusive container dependencies for parallel backup safety.

## Step 6: Add Backup Validation Check

Edit `aihub_backup/aihub_backup/dagster/assets/restore_session_factory.py`, function
`_validate_backup_completeness_or_raise()`:

Add a check for the new service's expected backup artifact in S3. Follow the existing patterns:

- Required files: `if not s3.file_exists(f"{timestamp}/{artifact}")` → append to `missing`
- Optional/recoverable: `context.log.warning(...)` without adding to `missing`

No separate restore op is needed — the `restore_service_factory` automatically creates restore assets for every entry in
`service_keys` in `definitions.py`.

## Step 7: Add Settings Fields

Edit `aihub_backup/aihub_backup/settings.py`:

Add connection credentials to `BackupSettings`. Use `SecretStr` for passwords/tokens. Follow the existing field naming
pattern (service-prefixed, matching compose env var names exactly).

## Step 8: Wire Compose Environment

Edit `deployment/templates/docker-compose.yml.j2`, in the `backup-code:` service `environment:` block:

Add env vars for the new service's credentials. Follow existing patterns:

- Internal Docker hostnames use Jinja2 variables: `{{ VARNAME }}`
- Secrets reference `.env` vars: `${VAR_NAME}`

Also add a `depends_on` entry if the backup service needs the new service's container.

After editing the template, run:

```bash
make generate-compose
```

## Step 9: Add .env Defaults

Edit `.env.dev` and `.env.prod`:

Add any new env vars referenced as `${VAR_NAME}` in the compose template:

- `.env.dev`: use development defaults (e.g., `"dev-password"`)
- `.env.prod`: use `"REPLACE_WITH_RANDOM_STRING"` for secrets

## Verification

Run the validation script to check registration points:

```bash
bash .claude/skills/add-backup-service/scripts/validate.sh {ServiceName}
```

Then run tests:

```bash
cd aihub_backup && make test
```

Finally, consider running the backup-coverage-checker agent to verify the new service is fully wired against the compose
template.

## Quick Reference

| Step | File                                                                  | What to add                                     |
| ---- | --------------------------------------------------------------------- | ----------------------------------------------- |
| 1    | `aihub_backup/aihub_backup/services/{name}.py`                        | Handler implementing `BackupHandler` ABC        |
| 2    | `aihub_backup/aihub_backup/models.py`                                 | `BACKUP_SERVICES` + `SERVICE_TO_ASSET_KEY`      |
| 3    | `aihub_backup/aihub_backup/dagster/assets/handler_factory.py`         | `HANDLER_FACTORIES` entry                       |
| 4    | `aihub_backup/aihub_backup/dagster/definitions.py`                    | Keys in `service_keys` + `restore_service_keys` |
| 5    | `aihub_backup/aihub_backup/container_lifecycle.py`                    | `SERVICE_DEPS` entry                            |
| 6    | `aihub_backup/aihub_backup/dagster/assets/restore_session_factory.py` | Validation check in `_validate_*`               |
| 7    | `aihub_backup/aihub_backup/settings.py`                               | Credential fields in `BackupSettings`           |
| 8    | `deployment/templates/docker-compose.yml.j2`                          | Env vars in backup block + `depends_on`         |
| 9    | `.env.dev` + `.env.prod`                                              | New env var defaults                            |
