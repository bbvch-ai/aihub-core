---
name: scaffold-pipeline
description: "Generate a new Dagster data pipeline using the two-stage factory pattern. Handles two scenarios: adding a new data source (using templates and definition builders) or extending the processing framework (new ops, resources, IO managers). Use when user says 'create a pipeline', 'scaffold pipeline', 'new data pipeline', 'add ingestion pipeline', 'generate Dagster pipeline', 'add a new source', 'connect SharePoint', 'connect OneDrive', or 'build a pipeline for X'. Do NOT use for pipeline architecture questions (use dagster-pipelines), debugging failures (use debug-pipeline), or rclone-specific config (use rclone-guide)."
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New Dagster Pipeline

Generate boilerplate for a new data pipeline. The pipeline name/purpose should be provided via `$ARGUMENTS`.

## Before You Start

Read these files to understand the patterns:

- `packages/pipeline/CLAUDE.md` -- scope architecture and folder structure
- `packages/pipeline/app/default_rag_pipeline/__init__.py` -- real app entry point (~18 lines)
- `packages/pipeline/templates/sources/README.md` -- source template guide with namespace explanation
- `packages/pipeline/playground/quick_start/my_document_pipeline.py` -- full manual wiring example

Determine which path applies:

- **Path A** (common): New data source -- connect a new external source (SharePoint, OneDrive, S3, etc.) to the existing
  processing pipeline
- **Path B** (rare): Custom processing -- extend the SDK framework with new ops, resources, or IO managers

______________________________________________________________________

## Path A: New Data Source

This is the most common scenario. The platform already handles parsing, chunking, embedding, and vector storage. You
just need to connect a new source.

### Step 1: Choose a Source Template

Check existing templates in `packages/pipeline/templates/sources/`:

| Template        | Source             | Factory Function                                   | RcloneSourceFactory     |
| --------------- | ------------------ | -------------------------------------------------- | ----------------------- |
| `sharepoint/`   | SharePoint Online  | `default_rclone_to_datalake_definitions`           | `sharepoint_source()`   |
| `onedrive/`     | OneDrive           | `default_rclone_to_datalake_definitions`           | `onedrive_source()`     |
| `s3/`           | AWS S3 / MinIO     | `default_rclone_to_datalake_definitions`           | `s3_source()`           |
| `azure_blob/`   | Azure Blob Storage | `default_rclone_to_datalake_definitions`           | `azure_blob_source()`   |
| `google_drive/` | Google Drive       | `default_rclone_to_datalake_definitions`           | `google_drive_source()` |
| `sftp/`         | SFTP               | `default_rclone_to_datalake_definitions`           | `sftp_source()`         |
| `local_fs/`     | Local/Network FS   | `default_local_filesystem_to_datalake_definitions` | N/A                     |

If the source matches one of these, use the template. For any other rclone-supported backend (70+), use the rclone
pattern with `RcloneSourceSettings.load("YOUR_SOURCE")` from
`packages/core/swiss_ai_hub/core/infrastructure/rclone/RcloneSourceFactory.py`.

For SharePoint via native MS Graph API (not rclone), use `default_sharepoint_to_datalake_definitions` from
`packages/pipeline/swiss_ai_hub/pipeline/util/definitions_util.py`.

### Step 2: Create the App Entry Point

Create a new directory in `packages/pipeline/app/<pipeline_name>/` with an `__init__.py`.

Follow the pattern from `packages/pipeline/app/default_rag_pipeline/__init__.py`:

```python
# packages/pipeline/app/<pipeline_name>/__init__.py
from swiss_ai_hub.core.infrastructure.logging import enable_logging

from swiss_ai_hub.pipeline.util.definitions_util import default_definitions

enable_logging()

defs = default_definitions(
    datalake_container_name="<bucket-name>",
    embedding_model_name="embedding/large",
    llm_model_name="text-generation/mini",
    with_summary_nodes=True,
    with_table_refinement=True,
    observe_job_hour=2,
    observe_job_minute=0,
)
```

For a source ingestion pipeline (Stage 1), use the appropriate definition builder instead:

```python
# Example: rclone-based source (OneDrive, S3, Azure, etc.)
from swiss_ai_hub.core.infrastructure.rclone.RcloneSourceFactory import onedrive_source

from swiss_ai_hub.pipeline.util.definitions_util import default_rclone_to_datalake_definitions

source = onedrive_source()

defs = default_rclone_to_datalake_definitions(
    datalake_container_name="<bucket-name>",
    datalake_directory_name="<namespace>",
    rclone_config=source,
    source_remote=f"{source.name}:",
)
```

### Step 3: Add Environment Variables

If the source needs credentials, add the required `RCLONE_` prefixed env vars to `.env.dev`. See the template's README
for which variables are needed (e.g., `templates/sources/sharepoint/README.md`).

The naming convention is `RCLONE_{SOURCE}_{OPTION}` (e.g., `RCLONE_SHAREPOINT_CLIENT_ID`). These are loaded by
`RcloneSourceSettings.load("SOURCE")` in `packages/core/swiss_ai_hub/core/infrastructure/rclone/RcloneSourceFactory.py`.

### Step 4: Create the Dockerfile

Copy and adapt `packages/pipeline/app/default_rag_pipeline/Dockerfile`. The only change needed is the `PIPELINE` build
arg:

```dockerfile
ARG PIPELINE=<pipeline_name>
```

The entrypoint uses this arg: `dagster api grpc -h 0.0.0.0 -p 4000 -m "app.${PIPELINE_NAME}"`

### Step 5: Register for Local Development

Add the new module to the Makefile's run command. In `packages/pipeline/Makefile`, the `rag-pipelines` target shows the
pattern:

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

Reference: `packages/pipeline/swiss_ai_hub/pipeline/io/S3DataLakeIOManager.py` (read+write),
`packages/pipeline/swiss_ai_hub/pipeline/io/RcloneIOManager.py` (read-only).

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

3. **Missing namespace config**: When using `default_rclone_to_datalake_definitions`, omitting `datalake_directory_name`
   means source folder structure becomes namespaces. Root-level files won't be indexed. See
   `packages/pipeline/templates/sources/README.md` for the namespace decision guide.

4. **Stale Dagster cache**: After changing asset definitions, Dagster may cache old metadata. Restart the dev server to
   pick up structural changes.
