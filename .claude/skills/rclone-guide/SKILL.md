---
name: rclone-guide
description: "Reference for the rclone source pipeline: how one deployed code location syncs every knowledge database whose source is rclone, RcloneSyncConfig (the announced per-database form covering six backends), source_config_for_bucket / rclone_remote_for_bucket (per-run resolution), RcloneClient (RC API), RoutedRcloneIOManager, the observable rclone asset, the registration and cleanup sensors, and how a synced file reaches the ingestion pipeline. Use when user says 'rclone configuration', 'sync from SharePoint/OneDrive/SFTP/S3', 'source pipeline', 'RcloneSyncConfig', 'rclone remote', 'rclone filter patterns', 'troubleshoot rclone', or 'how does rclone work'. Do NOT use for scaffolding new pipelines (use scaffold-pipeline), debugging pipeline failures (use debug-pipeline), or general pipeline architecture (use dagster-pipelines)."
allowed-tools: Read, Grep, Glob, Bash
---

# Rclone Source Pipeline — Reference

The rclone source pipeline is Stage 1 of knowledge ingestion: it pulls files from an external system into a knowledge
database's data lake. It is configured **per knowledge database from the UI**, not per deployment: a database carries a
`source` (`rclone`) and a `source_configuration` (backend, credentials, root folder, patterns), and one deployed
`rclone_pipeline` code location serves every such database. Nothing about a source lives in environment variables.

## Architecture

```
create-database dialog ──▶ API ──▶ BucketEntity{ingestor, configuration, source="rclone", source_configuration(enc)}
                                                                                         │ per-database schedule
SourcePipelineEntity ◀── registration sensor ── rclone_pipeline (Dagster) ──────────────┘
                                                   │ rclone_remote_for_bucket(): rebuild remote in the rclone daemon
                                                   │ list / download via RC API
                                                   ▼
                                    s3://{bucket}/{top folder}/{file}  ──▶ SourceUpdatedEvent ──▶ document_ingestion
```

- **Two axes per database.** `ingestor` says how files are processed (Stage 2), `source` says where they come from
  (Stage 1). `source = None` is manual upload.
- **Namespaces are generated.** Files land under `{bucket}/{top-level folder}/…`; the ingestion pipeline maps the first
  segment to a namespace. Files directly at the root of the chosen folder are skipped and counted in the observation.
- **Per-run routing.** The bucket travels in the `aihub/bucket` run tag (observe/remove) or the composite
  `{bucket}|{remote path}` partition key (write). One `rclone_source_partitions` registry, reconciled per bucket.

## Key Files

| Concern | Path |
| --- | --- |
| Announced form (all six backends) | `packages/pipeline/swiss_ai_hub/pipeline/source_pipelines/rclone_sync_config.py` |
| Per-run resolution | `packages/pipeline/swiss_ai_hub/pipeline/util/source_builders.py` |
| RC API client | `packages/pipeline/swiss_ai_hub/pipeline/resources/rclone/rclone_client.py` |
| IO manager (read-only) | `packages/pipeline/swiss_ai_hub/pipeline/io/routed_rclone_io_manager.py` |
| Observable asset | `packages/pipeline/swiss_ai_hub/pipeline/assets/factories/rclone_to_data_lake/observable_rclone_factory.py` |
| Partitions + versions | `packages/pipeline/swiss_ai_hub/pipeline/ops/rclone/data_version_by_partition_for_rclone_files.py` |
| Write + announce | `packages/pipeline/swiss_ai_hub/pipeline/ops/source/routed/` |
| Definitions factory | `packages/pipeline/swiss_ai_hub/pipeline/util/rclone_pipeline_definitions_util.py` |
| Deployed app | `packages/pipeline/app/rclone_pipeline/__init__.py` |
| Registration / cleanup sensors | `packages/pipeline/swiss_ai_hub/pipeline/sensors/source_pipeline_registration_sensor.py`, `source_bucket_cleanup_sensor.py` |
| Core: config base, record, entity | `packages/core/swiss_ai_hub/core/source_pipelines/`, `packages/core/swiss_ai_hub/core/persistence/rag/datalake/entities/source_pipeline*.py` |
| Settings | `packages/core/swiss_ai_hub/core/infrastructure/rclone/rclone_settings.py` (`RCLONE_URL`, `RCLONE_RC_USER/PASS`), `rclone_pipeline_settings.py` (`RCLONE_PIPELINE_OBSERVE_JOB_HOUR/MINUTE`, `MAX_PARTITIONS`) |

## RcloneSyncConfig (what a database stores)

```python
class RcloneSyncConfig(SourcePipelineConfig):
    backend_type: str | Select          # onedrive | drive | s3 | azureblob | sftp | local
    root_path: str | InputText          # folder inside the remote; its top-level folders become namespaces
    include_patterns: list[str] | ChipsInput   # rclone glob rules
    exclude_patterns: list[str] | ChipsInput
    onedrive: OneDriveOptions           # one nested Form per backend, shown only for the selected backend
    drive: GoogleDriveOptions
    s3: S3Options
    azureblob: AzureBlobOptions
    sftp: SftpOptions
    local: LocalOptions
```

- Every option group is non-nullable with primitive defaults, so a hidden group submits nothing and validates as its
  defaults; the group's `condition_if` is derived from its children (`$get(rclone_backend_type).value === 'sftp'`).
- Credentials are `str | Password`. `RcloneSyncConfig.secret_field_paths()` derives their dotted paths from the form;
  the API encrypts them (`SecretEncryptionService`) and returns a mask, the pipeline decrypts per run.
- `to_rclone_source_config(remote_name)` emits only the selected backend's non-empty options, renames `password` →
  `pass`, adds `client_credentials=true` for OneDrive without a token, and rejects a backend missing its required set.
- SharePoint is `onedrive` with `drive_type=documentLibrary`.
- Adding a backend = one `Form` subclass + one field + labels in
  `packages/core/swiss_ai_hub/core/i18n/translations/lib/source_pipelines.*.yml`. No API or UI change.

## Per-run resolution (`util/source_builders.py`)

```python
config = source_config_for_bucket(bucket, "rclone", RcloneSyncConfig)   # row → decrypt → validate; raises on mismatch
remote = rclone_remote_for_bucket(bucket, "rclone")                       # upserts remote "rclone_{bucket}" every call
client = build_rclone_client()                                            # stateless, RC URL + basic auth
files = run_async(client.list_files(remote.fs, include=remote.include_patterns, exclude=remote.exclude_patterns))
```

- The remote is **rebuilt on every run** with `config/create` (`obscure`, `nonInteractive`): credential edits apply on
  the next run and the daemon (`--config=/dev/null`, in-memory) needs no operator action after a restart.
- There are **no deployment defaults** for a source; a database without a valid source configuration must not sync.

## RcloneClient (RC API)

| Method | Endpoint | Notes |
| --- | --- | --- |
| `upsert_remote(config)` | `config/create` | replace semantics; raises if rclone asks an interactive question (OAuth without token) |
| `get_remote(name)` / `delete_remote(name)` | `config/get` / `config/delete` | |
| `list_files(remote, include, exclude)` | `operations/list` | filter rules: excludes, includes, then `- **` when includes exist |
| `download_bytes(remote, path)` | `operations/stat` + `GET /[remote]/path` | needs `--rc-serve` |

Secrets travel only in the `config/create` body; URLs, logs and Dagster metadata carry the remote **name**.

## Change detection

DataVersion = `hash:{md5|sha1|first}` when the backend reports hashes, else `mtime:{modified}-{size}`. New files get a
partition on the first observation and a version on the next; removed files disappear from the partition set and are
deleted from the data lake by `rclone_remove_source_files` (chained after the observation), which then announces each
removal to the ingestion pipeline.

## Deployment

- Service `rclone_pipeline` (compose template + `compose-config.yml` image tags; CI builds any `*_pipeline` with
  `build: localbuild`), Dagster workspace entry `rclone_pipeline:4000`.
- The `rclone` container sits on `backend` (reachable by the pipeline) and `egress` (reaches cloud providers).
- Env: `AIHUB_CONFIG_ENCRYPTION_KEY` (same as the API), `RCLONE_URL`, `RCLONE_RC_USER/PASS` (non-dev),
  `RCLONE_PIPELINE_OBSERVE_JOB_HOUR/MINUTE`.
- Dev: run `dagster dev` on the host with `app.rclone_pipeline`; the daemon is reachable at `RCLONE_URL=http://localhost:5572`.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Source not offered in the create dialog | `source_pipelines` collection has a row with `config_specs`; `SourcePipelineRegistrationSensorFor_rclone` running |
| Run fails "is filled by source 'x', not 'rclone'" / "being deleted" | the database's `source` changed or it is being torn down; the cleanup sensor forgets it |
| "needs an interactive step" | OAuth backend without a pre-obtained `token`; paste rclone's token JSON |
| Files listed but nothing ingested | they sit directly in `root_path` (root-level files are skipped) — move them into a folder |
| Nothing ingested after a sync | `pipeline_document_ingestion_stream` receives `SourceUpdatedEvent`s; the database's `ingestor` is registered |
| SFTP password rejected | must go through `config/create` with `obscure` (the client does this) |

## Conventions

- Never bake a bucket, remote or credential into `Definitions`; resolve per run through `source_builders`.
- Every deployment-global name derives from the `source` token; ingestor and source tokens reserve each other.
- Stage 1 never writes to the doc store or vector store; it announces and lets the ingestion pipeline reconcile.
