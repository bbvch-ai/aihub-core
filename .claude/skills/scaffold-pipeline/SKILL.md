---
name: scaffold-pipeline
description: Generate a new Dagster data pipeline with the two-stage pattern (source
  ingestion + unified processing). Creates assets, resources, I/O managers, and tests.
  Use when user says "create a pipeline", "scaffold pipeline", "new data pipeline",
  "add ingestion pipeline", "generate Dagster pipeline", or "build a pipeline for X".
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New Dagster Pipeline

Generate boilerplate for a new data pipeline. The pipeline name/purpose should be provided via `$ARGUMENTS`.

## Step 1: Read Reference Materials

1. Read the pipeline scope guide: `/home/user/aihub-core/aihub_pipeline/AGENTS.md`
2. Study existing pipelines in `aihub_pipeline/aihub_pipeline/pipelines/` for reference patterns
3. Extract the pipeline name from `$ARGUMENTS` and convert to `snake_case`

## Step 2: Create Pipeline Directory Structure

Create in `aihub_pipeline/aihub_pipeline/pipelines/<pipeline_name>/`:

```
<pipeline_name>/
├── __init__.py
├── assets.py         # Dagster asset definitions
├── resources.py      # Custom resources (API clients, configs)
├── io_managers.py    # Custom I/O managers if needed
└── ops.py           # Dagster ops for the pipeline
```

## Step 3: Implement the Two-Stage Pattern

The platform uses a two-stage pipeline pattern:

**Stage 1: Source Ingestion**
- Fetch data from external sources (APIs, files, databases)
- Normalize to internal format
- Store raw artifacts in SeaweedFS (S3-compatible)

**Stage 2: Unified Processing**
- Process ingested data
- Generate embeddings for vector search (Milvus)
- Create searchable indices

## Step 4: Define Assets Using the Factory Pattern

Use Dagster asset factories for reusable asset definitions:

- Define factory functions that create assets with configurable parameters
- Use `@asset` decorator with proper `group_name`, `compute_kind`, `metadata`
- Configure partitions if the pipeline processes data in chunks

## Step 5: Define Resources

Define Dagster resources for external dependencies:
- API clients (httpx.AsyncClient)
- Storage clients (SeaweedFS/S3)
- Database connections (Milvus, FerretDB)

## Step 6: Create Playground Configuration

Create a playground entry for local testing in `aihub_pipeline/playground/`.

## Step 7: Create Tests

Create in `aihub_pipeline/tests/pipelines/<pipeline_name>/`:
- `test_<pipeline_name>.py` -- Unit tests with mocked resources
- Test both asset materialization and error handling

## Key Patterns

- **Asset-based**: Use Dagster assets (not just ops) for data lineage
- **Idempotent**: Pipelines should be safe to re-run
- **Observable**: Add metadata to assets for Dagster UI visibility
- **Resource injection**: Use Dagster resources for external deps (testable)

## Examples

**Input**: `$ARGUMENTS = "confluence_sync - Pipeline to ingest Confluence wiki pages"`
**Expected output files**:
- `aihub_pipeline/aihub_pipeline/pipelines/confluence_sync/assets.py` with `@asset` definitions for ingestion and processing
- `aihub_pipeline/aihub_pipeline/pipelines/confluence_sync/resources.py` with Confluence API client resource
- `aihub_pipeline/tests/pipelines/confluence_sync/test_confluence_sync.py`

## Troubleshooting

- **Asset materialization fails**: Ensure resources are properly configured and injected via `@asset(required_resource_keys=...)`
- **Partition errors**: Verify partition definitions match the data source's natural partitioning (e.g., by date, by page)
- **I/O manager issues**: Check that custom I/O managers handle both load and store operations, and that `output_config` matches expectations
- **Playground not loading**: Verify the playground entry is properly registered in the Dagster definitions
