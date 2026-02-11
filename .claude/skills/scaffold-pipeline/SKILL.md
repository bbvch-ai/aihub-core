---
name: scaffold-pipeline
description: Generate a new Dagster data pipeline with the two-stage pattern
  (source ingestion and unified processing). Creates asset factories, I/O managers,
  resources, and playground configuration.
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New Dagster Pipeline

Generate boilerplate for a new data pipeline. The pipeline name/purpose should be provided via `$ARGUMENTS`.

## Before You Start

Read the pipeline scope guide: `/home/user/aihub-core/aihub_pipeline/AGENTS.md`

Study existing pipelines for reference patterns.

## What to Generate

### 1. Pipeline Directory Structure

Create in `aihub_pipeline/aihub_pipeline/pipelines/<pipeline_name>/`:

```
<pipeline_name>/
├── __init__.py
├── assets.py         # Dagster asset definitions
├── resources.py      # Custom resources (API clients, configs)
├── io_managers.py    # Custom I/O managers if needed
└── ops.py           # Dagster ops for the pipeline
```

### 2. Two-Stage Pattern

The platform uses a two-stage pipeline pattern:

**Stage 1: Source Ingestion**
- Fetch data from external sources (APIs, files, databases)
- Normalize to internal format
- Store raw artifacts in SeaweedFS (S3-compatible)

**Stage 2: Unified Processing**
- Process ingested data
- Generate embeddings for vector search (Milvus)
- Create searchable indices

### 3. Asset Factory Pattern

Use Dagster asset factories for reusable asset definitions:

- Define factory functions that create assets with configurable parameters
- Use `@asset` decorator with proper `group_name`, `compute_kind`, `metadata`
- Configure partitions if the pipeline processes data in chunks

### 4. Resources

Define Dagster resources for external dependencies:
- API clients (httpx.AsyncClient)
- Storage clients (SeaweedFS/S3)
- Database connections (Milvus, FerretDB)

### 5. Playground Configuration

Create a playground entry for local testing in `aihub_pipeline/playground/`.

### 6. Tests

Create in `aihub_pipeline/tests/pipelines/<pipeline_name>/`:
- `test_<pipeline_name>.py` — Unit tests with mocked resources
- Test both asset materialization and error handling

## Key Patterns

- **Asset-based**: Use Dagster assets (not just ops) for data lineage
- **Idempotent**: Pipelines should be safe to re-run
- **Observable**: Add metadata to assets for Dagster UI visibility
- **Resource injection**: Use Dagster resources for external deps (testable)
