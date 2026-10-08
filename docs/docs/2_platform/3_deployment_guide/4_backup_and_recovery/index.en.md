---
title: Backup and Recovery
---

# Backup and Recovery

## Overview

Swiss AI Hub includes an automated backup service that periodically dumps all stateful services to the internal
SeaweedFS S3 storage (`s3://backups/`). Backups run on a daily schedule (1 AM Europe/Zurich) with automatic retention
cleanup. The backup service is a standalone Dagster instance with a web UI for monitoring, manual triggers, and
parameterized restores.

Each instance has independent backups. Data isolation between instances. Recovery operations don't affect other
instances.

::: info Multi-instancing context
This chapter assumes a multi-instance deployment model where each organization has their own isolated Swiss AI Hub
instance. For multi-tenancy (logical separation within a single instance), see [Multi-tenancy](../../16_multi_tenancy/).
:::

______________________________________________________________________

## What gets backed up

| Service               | Method                                                   | Data                                              |
| --------------------- | -------------------------------------------------------- | ------------------------------------------------- |
| PostgreSQL (main)     | `pg_dumpall` + `pg_dump`                                 | OpenWebUI, Langfuse, Dagster, LiteLLM databases   |
| PostgreSQL (FerretDB) | `pg_dumpall` + `pg_dump` + `COPY` (DocumentDB catalog\*) | Agent configs, users, threads, tokens, RBAC roles |
| Milvus                | `milvus-backup` (official tool)                          | Vector collections with consistent metadata       |
| Neo4j                 | `neo4j-admin` via temp container                         | Agent memory graphs (Mem0)                        |
| ClickHouse            | `BACKUP TO Disk('backup_s3', ...)` SQL command           | Langfuse traces, observations, scores             |
| Valkey                | `BGSAVE` + RDB copy (+ temp container on restore)        | Cache and session state (RDB snapshot)            |
| NATS                  | `nats` CLI stream backup                                 | JetStream streams                                 |

### What is NOT backed up by the platform

**SeaweedFS bucket data** (user-uploaded documents, knowledge base files, chat attachments) is the responsibility of the
infrastructure layer. Use VM snapshots, rclone sync, or external S3 replication to protect this data. The platform
cannot back up SeaweedFS into itself.

`parse-cache` is derived data: it holds MinerU and MarkItDown results that are re-created on demand, so it needs no
backup.

`sandbox-files` is **not** derived data. It mirrors the code-sandbox homes (the users' **My Files**) so the files
survive the loss of the sandbox volume. Neither the sandbox volume nor this bucket is covered by the platform backup, so
the bucket is the only copy of My Files that outlives that volume. Include it when you protect SeaweedFS.

All service backups are required. A missing backup for any service will block the restore.

______________________________________________________________________

## Configuration

Configure the backup service via environment variables in `.env.dev` (development) or `.env.prod` (production):

```bash
BACKUP_RETENTION_DAYS="7"            # Keep backups for N days (dev: 7, prod: 30)
BACKUP_MINIMUM_KEEP="3"             # Minimum backups preserved regardless of age
BACKUP_S3_BUCKET="backups"           # S3 bucket name for backup storage
```

The backup schedule (daily at 1 AM Europe/Zurich) is defined in Dagster and can be toggled on/off via the Dagster UI.

::: warning Backup and pipeline schedules must not overlap
The backup stops all application containers, including the pipeline Dagster instance. The default schedules are
staggered: backup at 1:00 AM, pipeline observation at 2:00 AM, pipeline cleanup at 3:00 AM. If you change any schedule,
ensure the backup finishes before the first pipeline job starts — a backup running during a pipeline job kills it
mid-execution.
:::

______________________________________________________________________

## How backups work

Every backup stops all managed containers in parallel before taking snapshots, guaranteeing transactional consistency
across all databases. Containers with the prefixes `backup-`, `seaweedfs-`, `etcd`, and `traefik` are excluded from the
stop/start cycle — SeaweedFS is needed for S3 access, etcd for Milvus metadata, and Traefik for ingress availability
during backups.

Each service is dumped using its native backup tool. After all services are backed up, the platform restarts all
previously running containers in parallel. Docker Compose restart policies ensure services converge to a healthy state
even if some start before their dependencies are ready. If the backup fails mid-run, a failure hook automatically
restarts all managed containers as a safety measure.

To trigger a manual backup, open the Dagster UI at `http://localhost:3004`, navigate to the backup assets, and click
"Materialize".

### Neo4j sibling container

Neo4j Community Edition does not support online backups — `neo4j-admin database dump` requires exclusive access to the
`/data` directory and cannot run while the Neo4j process holds a lock on it. Because a stopped Docker container cannot
execute commands either, the backup service spins up a **temporary sibling container** using the same Neo4j image and
the same `/data` volume (both discovered automatically from the production container at runtime). The sibling runs
`neo4j-admin`, copies the dump file out, and is removed immediately afterward. A similar sibling is used for restore.

You may notice a short-lived container named `neo4j-dump-<id>` or `neo4j-restore-<id>` during backup/restore runs — this
is expected and cleaned up automatically.

### \* DocumentDB catalog workaround

PostgreSQL's `pg_dump` silently skips data for tables owned by extensions — it assumes `CREATE EXTENSION` will
repopulate them during restore. The DocumentDB extension (used by FerretDB's PostgreSQL backend) owns its catalog tables
(`documentdb_api_catalog.collections` and `collection_indexes`) but does not register them for dump inclusion. The usual
fix (`pg_extension_config_dump()`) cannot be called externally — PostgreSQL restricts it to `CREATE EXTENSION` scripts.

Without a workaround, a restore would have all document data intact but an empty catalog — FerretDB would report zero
collections. The backup service handles this automatically: during backup it separately extracts catalog rows using
`COPY TO STDOUT` into an `ext-catalog.sql.gz` artifact, and during restore it replays this SQL after `pg_restore`. No
operator action is required.

______________________________________________________________________

## Listing backups

Open the Dagster UI at `http://localhost:3004` to see the backup asset view, which shows backup history at a glance. The
asset metadata includes timestamp and S3 prefix for each backup.

______________________________________________________________________

## Recovery

### Full-system restore

Restores the entire platform to a specific backup. Stops all services, restores each database, then restarts all
containers.

To run a full restore, open the Dagster UI at `http://localhost:3004`, navigate to Jobs -> `full_restore_job`, select a
backup timestamp from the partition dropdown, and click "Launch Run".

The restore process follows three phases:

1. **Full stop**: All application and database containers are stopped (except SeaweedFS, which is needed for S3 access)
2. **Restore data**: Each service is restored from its backup. PostgreSQL instances are started temporarily for SQL
   import. Milvus is started temporarily for the milvus-backup restore API.
3. **Full start**: All previously running containers are restarted. Docker Compose restart policies ensure services
   converge to a healthy state even if some start before their dependencies are ready.

::: warning Restore failure behavior
On failure during restore, containers are intentionally **not** restarted automatically. The operator must investigate
the failure and decide whether to retry or restore from a different backup. This is a deliberate safety measure — an
automatic restart after a partial restore could leave the system in an inconsistent state.
:::

::: warning A backup taken before a Langfuse upgrade is not a rollback target
The restore validates only that the expected artifacts are **present**. It carries no schema-version stamp, so it will
happily restore a backup taken under an older Langfuse into a stack running a newer one.

Langfuse spans two stores that are restored by independent handlers: its Postgres database (`langfuse.dump`) and its
ClickHouse tables (`clickhouse/`). ClickHouse is captured with a native `BACKUP DATABASE`, so the restore reinstates the
**table definitions** as well as the data. Nothing checks that the two stores agree with each other, and no migration
step runs afterwards — the schema only moves forward again when the Langfuse containers next start.

Treat a Langfuse version bump as a one-way door: take a backup beforehand for data recovery, but plan forward recovery
rather than downgrade.
:::

### Users' sandbox files (My Files)

The users' homes in the code sandbox (the files behind My Files) live on the host volume mounted at
`<VOLUME_ROOT>/open-terminal`. The `sandbox-mirror` service copies them one way into the `sandbox-files` bucket every
`SANDBOX_MIRROR_INTERVAL_SECONDS`, keeping each file's owner, group, mode and modification time, and keeps a deleted or
overwritten file under `.deleted/<timestamp>/` for a week. The mirror protects against losing the homes volume, not
SeaweedFS itself; see [What is NOT backed up](#what-is-not-backed-up-by-the-platform).

To bring the homes back after the volume is lost:

1. Stop the mirror **first**, then the sandbox. A running mirror would copy the empty volume over the bucket and move
   every file into `.deleted/`.

   ```bash
   docker compose stop sandbox-mirror open-terminal
   ```

2. Copy the homes back, with the mirror's own credentials and the volume mounted writable:

   ```bash
   docker compose run --rm --no-deps \
     -v "<VOLUME_ROOT>/open-terminal:/restore" \
     --entrypoint rclone sandbox-mirror \
     copy mirror:sandbox-files /restore --metadata --exclude "/.deleted/**"
   ```

   Files come back with their owner and mode. Folders do not: the bucket holds no folder metadata, so each home comes
   back owned by `root` with mode `755` until the next step.

3. Recreate the sandbox, then start the mirror again. The new container provisions each user's account on their next
   request, which makes them the owner of their home again and sets it to `2770`, so only they can read it.

   ```bash
   docker compose up -d --force-recreate open-terminal
   docker compose up -d sandbox-mirror
   ```

   Skipping the recreate leaves every home owned by `root`: users cannot write to their own files, and other users can
   list them.

______________________________________________________________________

## VM snapshots

VM snapshots remain a valid complementary strategy, especially for protecting SeaweedFS data. They capture everything:
OS, Docker, data, configuration. You restore the entire VM in one operation.

Stop Swiss AI Hub services before creating a snapshot using `docker compose down`. Alternatively, use
application-consistent snapshots (Azure with VM agent, VMware with quiesce). Create snapshots before major updates.

______________________________________________________________________

## Continuous Postgres maintenance

The same Dagster instance that runs backup also runs **continuous Postgres health maintenance** so the platform's
`event_logs` and `runs` tables don't grow without bound on long-running deployments. Two additional jobs are wired into
the same backup Dagster UI at `http://localhost:3004`:

- **`dagster_cleanup_job`** — Sundays at 3 AM Europe/Zurich. Prunes verbose Python logs and curated framework-internal
  events (`HANDLED_OUTPUT`, `LOADED_INPUT`, `ENGINE_EVENT`, `ASSET_MATERIALIZATION_PLANNED`, `STEP_OUTPUT`) past their
  retention windows. Idempotently ensures the cleanup query indexes exist and applies tighter autovacuum tuning to the
  heavy tables.
- **`postgres_repack_job`** — first Sunday of each month at 4 AM. Runs `pg_repack` on `event_logs`, `runs`, and
  `job_ticks` to return disk pages to the OS (plain `VACUUM` only marks dead rows reusable internally).

**UI-safe by construction**: cleanup never deletes rows the Dagster UI depends on (`ASSET_MATERIALIZATION`,
`STEP_SUCCESS`, `STEP_FAILURE`, `RUN_SUCCESS`, `RUN_FAILURE`, the `runs` table, asset catalog, sensor cursors).

**Mutually exclusive with backup**: every job that touches Postgres carries a `postgres-mutex` tag. The backup Dagster's
run coordinator caps concurrency for that tag at one, so cleanup or repack ticks queue behind a still-running backup
instead of starting concurrently. Within each run, intra-run parallelism (e.g. parallel per-service backups) is
unaffected.

**`pg_repack` ships in the platform Postgres image**: the project-managed image extends `pgvector/pgvector:pg17` with
`postgresql-17-repack` and the extension is registered in the `dagster` database on first init. Deployments using a
foreign Postgres image without the extension still work — repack reports a clean skip in the run metadata; cleanup works
unconditionally.

### Configuration

```bash
# Retention windows (defaults follow the official Dagster docs recipe)
DAGSTER_DEBUG_LOG_RETENTION_DAYS="7"
DAGSTER_INFO_LOG_RETENTION_DAYS="60"
DAGSTER_WARNING_LOG_RETENTION_DAYS="60"
DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS="30"

# Per-DELETE row cap — protects against WAL-flooding on first run against a backlogged DB
DAGSTER_CLEANUP_BATCH_LIMIT="1000000"

# Kill switch — set to true and the maintenance handlers no-op; backup is unaffected
MAINTENANCE_DISABLED="false"

DAGSTER_DB="dagster"
POSTGRES_PORT="5432"
```

A heavily backlogged DB drains over multiple weekly ticks (`DAGSTER_CLEANUP_BATCH_LIMIT` rows per tick × 4 cleanup
handlers). Operators wanting a faster initial drain can manually launch `dagster_cleanup_job` repeatedly through the
Dagster UI.

______________________________________________________________________

## One-off: recompress FerretDB data with lz4

FerretDB's PostgreSQL (`postgres-ferretdb`) runs with `default_toast_compression=lz4`. DocumentDB decompresses a whole
document for every filter, projection and sort, and lz4 does that about three times faster than PostgreSQL's default
`pglz`. Knowledge content search and document listing get 2–4× faster. See the ADR
`2026_10_07_ferretdb_postgres_lz4_toast_compression`.

The setting applies to every row written after it is active. Rows written before keep pglz. They read correctly, just
more slowly, until they change. **`ferretdb_lz4_rewrite_job`** recompresses the existing pglz rows of every FerretDB
collection: knowledge stores, agent events, configurations and everything else. Run it once per deployment, after the
first deploy with the setting. It is launched by hand and never scheduled.

### Before you start

1. **Check that the setting is active.** This must print `lz4`:

   ```bash
   docker exec postgres-ferretdb psql -U "$MONGO_USERNAME" -d postgres -Atc 'show default_toast_compression'
   ```

   If it prints `pglz`, recreate the container with the same compose file, project directory and env file your
   deployment always uses, for example `docker compose -f infra/docker-compose.<stage>.yml --env-file .env up -d
   postgres-ferretdb` from the repository root. FerretDB is unavailable for a few seconds while it is recreated.
   `docker restart` is not enough, because it keeps the container's old command.

   ::: warning
   The data directory (`VOLUME_ROOT`, by default `./.docker-volumes`) is resolved relative to the compose file's
   folder. A compose file from another checkout or folder mounts an **empty** data directory, and FerretDB then serves
   an empty instance. Afterwards, check in the output of `docker inspect postgres-ferretdb` that `Mounts` → `Source`
   is your usual data directory.
   :::

   Nothing has to be installed: the platform's `postgres-ferretdb` image is built with lz4 support. If your deployment
   replaced that image with its own, check it first with `docker exec postgres-ferretdb pg_config --configure`, which
   must list `--with-lz4`; without it, PostgreSQL refuses to start with the setting.

2. **Check how much work there is and how much disk it needs.** Run this inside
   `docker exec -it postgres-ferretdb psql -U "$MONGO_USERNAME" -d postgres`; `\gexec` runs one count per collection:

   ```sql
   select format(
       'select %L as collection, count(*) filter (where pg_column_compression(document) = ''pglz'') as pglz_rows, '
       'pg_size_pretty(pg_total_relation_size(%L)) as size from documentdb_data.documents_%s',
       database_name || '.' || collection_name, 'documentdb_data.documents_' || collection_id, collection_id)
   from documentdb_api_catalog.collections where view_definition is null \gexec
   ```

   Plan free space of about a fifth of the size of the collections with pglz rows: the rewritten tables grow by about a
   tenth and keep that size.

3. **Pick a quiet window**: no backup due and no large ingestion running.

### Run the job

1. In the backup Dagster UI (`http://localhost:3004`), open **Jobs → `ferretdb_lz4_rewrite_job`** and launch it. It
   stays *Queued* while a backup, restore, cleanup or repack holds the `postgres-mutex`.
2. **Check the run's metadata** when it finishes:
   - `pglz_rows_after` is `0`;
   - `collections_rewritten` lists the collections it rewrote, as `database.collection`;
   - `collections_skipped` counts those that had no pglz rows.
3. **Optionally launch it again.** Every collection is now skipped, which confirms the migration is complete.

The job runs online, in SQL against the tables behind FerretDB. For each collection that still has pglz rows, it:

- replaces 50 rows at a time with a copy of the same bytes (`bson_from_bytea(bson_to_bytea(document))`), which
  PostgreSQL compresses with lz4. The documents do not change, so applications reading them see nothing;
- selects only rows that are still pglz, so a row FerretDB rewrote meanwhile is left as it is;
- runs `VACUUM` every 500 rows, or every 2% of the collection's pglz rows when that is more, so the space of the
  replaced row versions is reused, and `VACUUM (ANALYZE)` at the end.

Ingestion and agents can keep writing meanwhile.

### What to expect

- **Duration:** on the dev stack, 18,900 rows in 8 collections (690 MB, mostly knowledge documents of 100k characters
  and agent events) took 31 seconds. Each row is written once; the WAL this produces is recycled at checkpoints, so it
  does not need extra disk of the data's size. On large deployments, run it outside ingestion peaks anyway: it competes
  for PostgreSQL's cache, so searches are slower while it runs.
- **Disk usage grows a little and stays.** The same run grew those tables from 690 to 761 MB (+10%). VACUUM makes space
  reusable inside PostgreSQL but does not return it to the OS; new data fills it over time. `VACUUM FULL` would return
  it at once, but its exclusive lock blocks FerretDB, so never run it during working hours.
- **Restores** write every row with the target server's default. A restore onto a server with the setting needs no
  rewrite afterwards; a restore onto a server without it brings pglz back.

### If it stops part-way

Each batch of 50 rows is its own transaction, and only rows that are still pglz are selected. A run interrupted by a
deploy, a lost connection or a full disk leaves every row either as it was or recompressed, never half-written. Launch
it again and it continues with the rows that are left.

### Common errors

| Symptom                                                 | Cause                                                                                            | Fix                                                                                     |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| Fails with `default_toast_compression is pglz, not lz4` | The setting is not active: the deploy did not run, or the container was restarted, not recreated | Recreate `postgres-ferretdb` with `up -d` as above, then launch again                   |
| Stays *Queued*                                          | Another Postgres job holds the mutex                                                             | Wait; don't cancel the backup                                                           |
| Succeeds with `skipped: MAINTENANCE_DISABLED`           | `BACKUP_MAINTENANCE_DISABLED` is `true`                                                          | Set it to `false` for the run                                                           |
| Connection refused to `postgres-ferretdb:5432`          | PostgreSQL is down, or a customised compose file took `backup-code` off the `data` network      | Start `postgres-ferretdb`, or restore the network                                       |
| Fails with `N rows are still pglz after the rewrite`    | A table pins its own compression (`ALTER TABLE … SET COMPRESSION pglz`), which wins over the default | Reset it with `ALTER TABLE … ALTER COLUMN document SET COMPRESSION DEFAULT`, then launch again |
| Fails part-way (disk full, deploy, lost connection)     | The run was interrupted                                                                          | Free space if needed, then launch again; it continues with the rows still pglz          |

Recompressing by hand with `UPDATE … SET document = document` does not work: PostgreSQL copies the compressed value
unchanged.

**Rollback** means removing the `-c default_toast_compression=lz4` flag from `postgres-ferretdb`. New rows are then pglz
again, and lz4 rows stay readable, so nothing has to be migrated back. Every future `postgres-ferretdb` image must be
built with lz4 support (`pg_config --configure | grep lz4`).

______________________________________________________________________

## Backup storage layout

Each backup is stored in a flat, timestamped directory:

```
s3://backups/
  2026-02-17_02-00-00/
    postgres-main/
      globals.sql.gz
      openwebui.dump
      langfuse.dump
      dagster.dump
      litellm.dump
    postgres-ferretdb/
      globals.sql.gz
      ferretdb.dump
      ext-catalog.sql.gz
    milvus_backup_2026_02_17_02_00_00/...
    neo4j.dump
    clickhouse/
      backup_2026_02_17_02_00_00/...
    valkey.rdb
    nats-jetstream.tar.gz
  2026-02-18_02-00-00/
    ...
```

______________________________________________________________________
