---
name: scaffold-pipeline
description: "Generate a new Dagster data pipeline using the two-stage factory pattern. Handles two scenarios: connecting a new data source (per-database source configuration, a new rclone backend, or a new source pipeline type) or extending the processing framework (new ops, resources, IO managers). Use when user says 'create a pipeline', 'scaffold pipeline', 'new data pipeline', 'add ingestion pipeline', 'generate Dagster pipeline', 'add a new source', 'connect SharePoint', 'connect OneDrive', or 'build a pipeline for X'. Do NOT use for pipeline architecture questions (use dagster-pipelines), debugging failures (use debug-pipeline), or rclone-specific config (use rclone-guide)."
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New Dagster Pipeline

Generate boilerplate for a new data pipeline. The pipeline name/purpose should be provided via `$ARGUMENTS`.

## Before You Start

Read these files to understand the patterns:

- `packages/pipeline/CLAUDE.md` -- scope architecture and folder structure
- `packages/pipeline/app/document_ingestion_pipeline/__init__.py` -- real app entry point (~18 lines)
- `packages/pipeline/app/rclone_pipeline/__init__.py` -- the rclone source pipeline app (~7 lines)
- `packages/pipeline/swiss_ai_hub/pipeline/source_pipelines/rclone_sync_config.py` -- the announced per-database source
  form (one nested `Form` per backend)
- `packages/pipeline/playground/quick_start/my_document_pipeline.py` -- full manual wiring example

Determine which path applies:

- **Path A** (common): New data source -- connect an external source (SharePoint, OneDrive, S3, etc.) to the existing
  processing pipeline. Usually needs **no code**: sources are configured per database in the UI.
- **Path B** (rare): Custom processing -- extend the SDK framework with new ops, resources, or IO managers

______________________________________________________________________

## Path A: New Data Source

This is the most common scenario. The platform already handles parsing, chunking, embedding, and vector storage. You
just need to connect a new source.

### Step 1: Check Whether the Source Is Already Covered

Sources are configured **per knowledge database in the create dialog** through the rclone source pipeline
(`app/rclone_pipeline`, one deployment for every database whose `source` is `rclone`). The user picks a **Source**,
selects a backend and enters credentials, root folder and patterns; nothing is deployed and no env var is set.

| Backend (`backend_type`) | Source                            | Options `Form`        |
| ------------------------ | --------------------------------- | --------------------- |
| `onedrive`               | OneDrive / SharePoint (`drive_type=documentLibrary`) | `OneDriveOptions`     |
| `drive`                  | Google Drive                      | `GoogleDriveOptions`  |
| `s3`                     | AWS S3 / MinIO / S3-compatible    | `S3Options`           |
| `azureblob`              | Azure Blob Storage                | `AzureBlobOptions`    |
| `sftp`                   | SFTP                              | `SftpOptions`         |
| `local`                  | Path inside the rclone container  | `LocalOptions`        |

If the source is one of these, **stop here**: create the database from the UI with that source. Each top-level folder
under the root becomes a namespace; root-level files are skipped.

**Adding another rclone backend** (rclone supports 70+): in `source_pipelines/rclone_sync_config.py` add one `Form`
subclass with the backend's options (credentials as `str | Password`, `condition_if=_when(backend)`), one field on
`RcloneSyncConfig` with a `default_factory`, an entry in `_require`, the backend in `RcloneBackendType`
(`packages/core/swiss_ai_hub/core/infrastructure/rclone/`), and labels in
`packages/core/swiss_ai_hub/core/i18n/translations/lib/source_pipelines.{en,de,fr,it}.yml`. No API or UI change; the
form is re-announced by the registration sensor.

**A whole new source pipeline type** (not rclone): a `SourcePipelineConfig` subclass in `source_pipelines/`, an
observable factory that resolves the bucket from the `aihub/bucket` run tag, a read-only routed IO manager, per-run
resolution in the style of `util/source_builders.py`, and a `rclone_pipeline_definitions`-style factory with its own
`source` token that wires `source_pipeline_registration_sensor`, `source_bucket_cleanup_sensor`,
`per_bucket_observe_schedule(owns=owned_by_source(source))` and the routed `source_to_data_lake` factories. Ingestor
and source tokens reserve each other; the factory raises at build time for a reserved id or missing labels.

For SharePoint via native MS Graph API (not rclone), the deploy-time `default_sharepoint_to_datalake_definitions` from
`packages/pipeline/swiss_ai_hub/pipeline/util/definitions_util.py` still exists and binds one bucket.

### Step 2: Create the App Entry Point

Create a new directory in `packages/pipeline/app/<pipeline_name>/` with an `__init__.py`.

Follow the pattern from `packages/pipeline/app/document_ingestion_pipeline/__init__.py`:

```python
# packages/pipeline/app/<pipeline_name>/__init__.py
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import DocumentIngestionPipelineSettings, enable_logging

from swiss_ai_hub.pipeline.util.document_ingestion_definitions_util import document_ingestion_pipeline_definitions

enable_logging()

defs = document_ingestion_pipeline_definitions(
    # Routing key: this pipeline serves every knowledge database whose BucketEntity names it, and
    # namespaces every deployment-global Dagster name. Labels are required for a custom ingestor —
    # a sensor publishes them so the create-database dialog can offer it.
    ingestor="<ingestor_id>",
    display_name=LocaleString(en="<Display name>"),
    description=LocaleString(en="<What it does>"),
    # Models, enrichment switches and observation schedule this deployment defaults to, from
    # DOCUMENT_INGESTION_*; every knowledge database overrides them in the announced form.
    settings=DocumentIngestionPipelineSettings(),
)
```

Do not give a Stage-2 pipeline a fixed bucket: the target is resolved per run, so a new knowledge database needs no code
location, compose service or env var.

For a source pipeline (Stage 1), the shipped app is the whole pattern:

```python
# packages/pipeline/app/rclone_pipeline/__init__.py
from swiss_ai_hub.core.infrastructure import RclonePipelineSettings, enable_logging

from swiss_ai_hub.pipeline.util.rclone_pipeline_definitions_util import rclone_pipeline_definitions

enable_logging()

defs = rclone_pipeline_definitions(settings=RclonePipelineSettings())
```

A custom source pipeline type passes `source="<source_id>"`, `display_name`, `description` and its own
`SourcePipelineConfig.as_form()` as `config`. Never give a Stage-1 pipeline a bucket, remote or credential: they are
read from `BucketEntity.source_configuration` per run.

### Step 3: Environment Variables

A source needs none. Credentials are entered in the create dialog, encrypted by the API with
`AIHUB_CONFIG_ENCRYPTION_KEY` and decrypted by the pipeline with the same key, so the pipeline container carries that
key plus `RCLONE_URL`, `RCLONE_RC_USER/PASS` and the schedule (`RCLONE_PIPELINE_OBSERVE_JOB_HOUR/MINUTE`). Nothing
source-specific goes into `.env.dev`.

### Step 4: Create the Dockerfile

Copy and adapt `packages/pipeline/app/document_ingestion_pipeline/Dockerfile`. The only change needed is the `PIPELINE`
build arg:

```dockerfile
ARG PIPELINE=<pipeline_name>
```

The entrypoint uses this arg: `dagster api grpc -h 0.0.0.0 -p 4000 -m "app.${PIPELINE_NAME}"`

### Step 5: Register for Local Development

Add the new module to the Makefile's run command. In `packages/pipeline/Makefile`, the `document-ingestion-pipeline`
target shows the pattern:

```makefile
my-pipelines:
	OTEL_ENABLED=false uv run dagster dev -m app.<pipeline_name>
```

### Step 6: Verify

1. Start the pipeline locally: `cd packages/pipeline && uv run dagster dev -m app.<pipeline_name>`
2. Open Dagster UI at http://localhost:3000
3. Verify all assets, sensors, schedules, and jobs appear
4. Trigger the observable source asset manually (click Observe)
5. Confirm downstream assets auto-materialize

______________________________________________________________________

## Path B: Custom Processing (Extend the SDK)

Use this path when you need processing logic beyond what the standard pipeline provides (e.g., custom document
transformations, new storage backends, additional enrichment steps).

### Step 1: Create New Ops

Create ops in `packages/pipeline/swiss_ai_hub/pipeline/ops/<category>/`. Follow the conventions:

- Use `@op(code_version="v1")` for change detection
- Use `ResourceParam[T]` for resource injection (NOT `required_resource_keys`)
- Use `RetryPolicy(max_retries=6, delay=1, backoff=Backoff.EXPONENTIAL)` for external calls
- Typed inputs and outputs

Reference: `packages/pipeline/swiss_ai_hub/pipeline/ops/nodes/embed_nodes.py` (retry pattern),
`packages/pipeline/swiss_ai_hub/pipeline/ops/data_lake/parse_document_from_data_lake.py` (basic pattern).

### Step 2: Create Asset Factory

Create a factory function in `packages/pipeline/swiss_ai_hub/pipeline/assets/factories/<category>/`. The factory returns
a `@graph_asset` that composes your ops:

```python
@graph_asset(
    key=key,
    partitions_def=partitions,
    ins={"upstream": AssetIn(key=upstream_key)},
    automation_condition=AutomationCondition.eager(),
)
def my_asset(upstream: InputType) -> Output[OutputType]:
    result = my_op_1(upstream)
    return my_op_2(result)
```

Reference: `packages/pipeline/swiss_ai_hub/pipeline/assets/factories/data_lake_to_vector_store/documents_factory.py`.

### Step 3: Create Resources (If Needed)

Create resources in `packages/pipeline/swiss_ai_hub/pipeline/resources/<category>/`. Extend `ConfigurableResource`:

Reference: `packages/pipeline/swiss_ai_hub/pipeline/resources/parser/DocumentParserResource.py`.

Add the resource to the factory dict in `packages/pipeline/swiss_ai_hub/pipeline/resources/factory.py`.

### Step 4: Create IO Manager (If Needed)

If you need a new storage backend, create an IO manager in `packages/pipeline/swiss_ai_hub/pipeline/io/`. Extend
`ConfigurableIOManager` with `handle_output()` and `load_input()`. Handle both partitioned and non-partitioned cases.

Source connectors (read-only) should raise `NotImplementedError` in `handle_output()`.

Reference: `packages/pipeline/swiss_ai_hub/pipeline/io/s3_data_lake_io_manager.py` (read+write),
`packages/pipeline/swiss_ai_hub/pipeline/io/routed_rclone_io_manager.py` (read-only, bucket resolved per run).

### Step 5: Wire Into Definitions

Either extend `packages/pipeline/swiss_ai_hub/pipeline/util/definitions_util.py` with a new definition builder function,
or create the `Definitions` object directly in your app entry point (see
`packages/pipeline/playground/quick_start/my_document_pipeline.py` for the manual wiring pattern).

Every `Definitions` must include:

- `default_automation_sensor(assets)` from `packages/pipeline/swiss_ai_hub/pipeline/sensors/factory.py`
- `default_process_executor()` from `packages/pipeline/swiss_ai_hub/pipeline/executors/factory.py`

### Step 6: Test in Playground

Add a playground entry in `packages/pipeline/playground/` and run `make playground` to test interactively at
http://localhost:3000.

### Step 7: Create App Entry Point and Dockerfile

Same as Path A Steps 4-5. Create `app/<pipeline_name>/__init__.py` and `app/<pipeline_name>/Dockerfile`.

______________________________________________________________________

## Common Mistakes

1. **Forgetting the automation sensor**: Without `default_automation_sensor(assets)` in `Definitions.sensors`,
   `AutomationCondition.eager()` on assets won't trigger. Check
   `packages/pipeline/swiss_ai_hub/pipeline/sensors/factory.py`.

2. **Wrong resource keys**: The `resources` dict keys must match what ops expect via `ResourceParam[T]`. Common keys:
   `document_parser`, `node_parser`, `embedding_model`, `language_model`, `data_lake_client`, `data_lake_file_system`.

3. **Root-level files**: The rclone source pipeline maps each top-level folder under the database's `root_path` to a
   namespace; files directly in the root are skipped and counted in the observation. Point `root_path` one level up, or
   move the files into a folder.

4. **Stale Dagster cache**: After changing asset definitions, Dagster may cache old metadata. Restart the dev server to
   pick up structural changes.
