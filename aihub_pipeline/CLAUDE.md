# aihub_pipeline - Data Ingestion & Processing SDK

**Purpose**: Dagster-based SDK for document ingestion, parsing, embedding generation, and vector storage. Three parts:
the framework (`aihub_pipeline/`), deployable pipeline apps (`app/`), and playground examples (`playground/`). Prepares
data for RAG agents — agents query the output (Milvus vectors, MongoDB documents), they don't use this SDK directly.
Pre-configured source templates in `templates/` for quick onboarding.

## Folder Structure

```
aihub_pipeline/                        # SDK framework
├── assets/factories/                  # Asset factory functions (core building blocks)
│   ├── data_lake_to_vector_store/     # Stage 2: documents, nodes, summary_nodes, removed_documents
│   ├── source_to_data_lake/           # Stage 1 generic: data_lake_file, placeholder_refdocs, removed_data_lake_files
│   ├── share_point_to_data_lake/      # Stage 1: observable_share_point
│   ├── rclone_to_data_lake/           # Stage 1: observable_rclone
│   └── local_files_system_to_data_lake/  # Stage 1: observable_local_file_system
├── io/                                # I/O managers (storage handlers)
│   ├── S3DataLakeIOManager.py         # S3/MinIO/SeaweedFS
│   ├── AzureDataLakeIOManager.py      # Azure Data Lake Storage
│   ├── DocStoreIOManager.py           # MongoDB document store
│   ├── VectorStoreIOManager.py        # Milvus vector store
│   ├── SharePointIOManager.py         # SharePoint (read-only)
│   ├── RcloneIOManager.py             # Rclone 70+ backends (read-only)
│   └── LocalFileSystemIOManager.py    # Local/network filesystem (read-only)
├── ops/                               # Operations (@op processing steps)
│   ├── data_lake/                     # Parsing, versioning, figure descriptions, table refinement
│   ├── document/                      # RefDoc insertion, cleanup, metadata, placeholders
│   └── nodes/                         # Chunking, embedding, vector insertion, summaries
├── resources/                         # External dependencies (ConfigurableResource subclasses)
│   ├── data_lake/base/                # AbstractDataLakeClient, AbstractDataLakeClientResource
│   ├── data_lake/s3/                  # S3DataLakeClient, S3DataLakeFileSystemResource
│   ├── data_lake/azure/               # AzureDataLakeClient, AzureDataLakeFileSystemResource
│   ├── parser/                        # DocumentParserResource, MarkdownStructuralNodeParserResource, etc.
│   ├── vector_store/                  # MilvusVectorStoreResource
│   ├── doc_store/                     # MongoDocumentStoreResource
│   ├── llm/                           # EmbeddingModelResource, LanguageModelResource
│   ├── share_point/                   # SharePointResource (MS Graph API)
│   ├── rclone/                        # RcloneResource, RcloneClient (RC API)
│   ├── local_file_system/             # LocalFileSystemResource
│   └── factory.py                     # Resource factory functions (assembles resource dicts)
├── sensors/
│   ├── factory.py                     # default_automation_sensor (auto-materialization)
│   └── nats/nats_document_uploaded_sensor.py  # NATS event-driven triggers
├── schedules/factory.py               # daily_schedule_at, default_daily_materialize_schedule
├── jobs/factory.py                    # observe_source_job, materialize_asset_job, materialize_all_job
├── executors/factory.py               # default_process_executor (in-process)
├── automation/all_deps_completed.py   # AutomationCondition for all-deps-ready
├── types/                             # Domain types (Pydantic models)
│   ├── DataLakeFile.py                # File in cloud storage (S3 bucket)
│   ├── RefDocDocument.py              # Parsed document (extends LlamaIndex Document)
│   ├── SourceFile.py                  # Generic source file interface + MinimalSourceFile
│   ├── SharePointFile.py              # SharePoint-specific file
│   ├── RcloneFile.py                  # Rclone-specific file (70+ cloud backends)
│   └── FigureMetadata.py              # Image/figure metadata
├── util/                              # Utilities
│   ├── definitions_util.py            # default_definitions() + source-specific builders (CRITICAL)
│   ├── id_utils.py                    # uri_to_id() — URI to document ID (MD5 hash)
│   ├── partition_utils.py             # replace_partition_keys() — dynamic partition management
│   ├── bucket_utils.py                # get_db_name_from_bucket_name() — S3 bucket → MongoDB name
│   ├── key_utils.py                   # group_name_from_asset_key() — asset group derivation
│   └── meta_utils.py                  # data_lake_metadata_table() — Dagster UI formatting
└── const/pipeline_names.py            # INTERNAL_DATALAKE, INTERNAL_KNOWLEDGE_DB

app/                                   # Deployable pipelines (Dagster gRPC code locations)
├── default_rag_pipeline/              # Per-tenant bucket pipeline
│   ├── __init__.py                    # defs = default_definitions(DEFAULT_BUCKET_NAME)
│   └── Dockerfile                     # dagster api grpc on port 4000
└── shared_rag_pipeline/               # Shared bucket pipeline
    ├── __init__.py                    # defs = default_definitions(SHARED_BUCKET_NAME)
    └── Dockerfile

playground/                            # Examples (START HERE)
├── __init__.py                        # defs = default_definitions("playground")
└── quick_start/                       # Tutorials
    ├── simple_pipeline.py             # Hello-world: 2 basic assets, no external deps
    └── my_document_pipeline.py        # Full RAG pipeline with all factories

templates/sources/                     # Pre-configured source templates (7 backends)
├── sharepoint/                        # SharePoint Online
├── onedrive/                          # OneDrive (Personal/Business)
├── s3/                                # AWS S3 / MinIO / S3-compatible
├── azure_blob/                        # Azure Blob Storage
├── google_drive/                      # Google Drive
├── sftp/                              # SFTP (legacy systems)
└── local_fs/                          # Mounted network shares (NFS, SMB)
```

## Two-Stage Pipeline Architecture

Source-specific ingestion, then unified processing. This is the core architectural insight.

**Stage 1 (Source → Data Lake)**: Per-source pipelines. An observable asset monitors an external source for changes,
downloads files to the S3-compatible data lake (SeaweedFS). Each file becomes a dynamic partition. A cleanup asset
removes orphaned data lake files when source files are deleted.

Concrete Stage 1 flows (each uses `data_lake_file_factory` + a source-specific observable):

- SharePoint → S3 (`observable_share_point_factory`)
- Rclone (70+ backends: OneDrive, GDrive, Azure, Dropbox, etc.) → S3 (`observable_rclone_factory`)
- Local/network filesystem → S3 (`observable_local_file_system_factory`)

**Stage 2 (Data Lake → Vector Store)**: Unified pipeline, source-agnostic. All data lake files flow through the same
processing chain regardless of origin:

- `observable_data_lake_factory` → monitors S3 for new/changed files
- `documents_factory` → parse (MinerU) → `RefDocDocument` → MongoDB
- `nodes_factory` → chunk (MD structural) → embed → `TextNode[]` → Milvus
- `summary_nodes_factory` (optional) → hierarchical summaries → Milvus
- `removed_documents_factory` → cleanup orphaned documents

## The `default_definitions()` Function

The primary entry point for creating pipelines. Located in `util/definitions_util.py`. Returns a complete `Definitions`
object with all assets, resources, sensors, jobs, and schedules wired together.

```python
defs = default_definitions(
    datalake_container_name="my-bucket",              # S3 bucket name (required)
    embedding_model_name="embedding/large",            # LiteLLM model for embeddings
    llm_model_name="text-generation/mini",             # LiteLLM model for text generation
    with_summary_nodes=True,                           # Hierarchical RAG summaries
    with_table_refinement=True,                        # LLM table detection/splitting
    with_figure_descriptions=True,                     # Vision LLM for image descriptions
    document_parser_loader_type=LoaderType.MINERU,      # MinerU (default) or DocumentIntelligence
    max_partitions=1000,                               # Max partitions added/deleted per tick
)
```

Source-specific definition builders for Stage 1 (combine with `default_definitions()` for end-to-end):

- `default_sharepoint_to_datalake_definitions(...)` — SharePoint → S3
- `default_local_filesystem_to_datalake_definitions(...)` — Local FS → S3
- `default_rclone_to_datalake_definitions(...)` — Any rclone backend → S3

## Asset Factory Pattern

All factories return `graph_asset` (multi-op composition). They compose `@op` steps into a single asset:

```python
def my_factory(key: AssetKey, upstream_key: str | AssetKey, partitions: DynamicPartitionsDefinition) -> graph_asset:
    @graph_asset(
        key=key,
        partitions_def=partitions,
        ins={"upstream": AssetIn(key=upstream_key)},
        automation_condition=AutomationCondition.eager(),
    )
    def my_asset(upstream: InputType) -> Output[OutputType]:
        result = op1(upstream)
        return op2(result)
    return my_asset
```

Key factories (all in `assets/factories/`):

- **Stage 1**: `observable_*_factory` (source monitoring), `data_lake_file_factory` (source → DataLakeFile),
  `removed_data_lake_files_factory` (cleanup), `placeholder_refdocs_factory` (placeholder documents)
- **Stage 2**: `observable_data_lake_factory`, `documents_factory`, `nodes_factory`, `summary_nodes_factory`,
  `removed_documents_factory`

## Domain Types

| Type             | Base                  | Key Fields                                             | Storage                         |
| ---------------- | --------------------- | ------------------------------------------------------ | ------------------------------- |
| `DataLakeFile`   | `BaseModel`           | name, namespace, uri, hash, content, filetype          | S3 via DataLakeIOManager        |
| `RefDocDocument` | LlamaIndex `Document` | namespace, hash, uri, updated (computed from metadata) | MongoDB via DocStoreIOManager   |
| `TextNode`       | LlamaIndex `TextNode` | Used directly — not subclassed                         | Milvus via VectorStoreIOManager |
| `SourceFile`     | `BaseModel`           | name, path, size, modified, content                    | In-memory (not persisted)       |
| `SharePointFile` | `SourceFile`          | + download_url, full_url                               | via SharePointIOManager         |
| `RcloneFile`     | `SourceFile`          | + remote, remote_path, hashes, mime_type               | via RcloneIOManager             |

`DataLakeFile.from_content(uri, content, metadata)` — factory method for creating from raw bytes. `id_` is computed as
`uri_to_id(uri)` (MD5 hash). `RefDocDocument.add_metadata_from_data_lake_file()` enriches documents with standard
metadata keys (`NAMESPACE`, `HASH`, `SOURCE`, `CREATED_AT`, `UPDATED_AT`, `DOCUMENT_TITLE`, etc.).

## I/O Managers

All extend `ConfigurableIOManager` with `handle_output()` and `load_input()`. Support partitioned and non-partitioned
assets.

**Read/Write** (data lake and downstream storage):

- `S3DataLakeIOManager` — S3/MinIO/SeaweedFS. Metadata stored as S3 object tags.
- `AzureDataLakeIOManager` — Azure Data Lake Storage. URL-quoted metadata encoding.
- `DocStoreIOManager` — MongoDB via LlamaIndex `KVDocumentStore`. URI → document ID via `uri_to_id()`.
- `VectorStoreIOManager` — Milvus. Upsert mode. 30s retry logic for eventual consistency. Filters by `DOCUMENT_ID`.

**Read-Only** (source connectors — `handle_output()` raises `NotImplementedError`):

- `SharePointIOManager` — MS Graph API. Returns `SharePointFile` (partitioned) or `list[MinimalSharePointFile]`.
- `RcloneIOManager` — Rclone RC API. Returns `RcloneFile` (partitioned) or `list[MinimalRcloneFile]`.
- `LocalFileSystemIOManager` — Pattern-based FS scanner. Returns `SourceFile` or `list[MinimalSourceFile]`.

## Resources

**Data lake hierarchy** (cloud-agnostic abstraction):

- `AbstractDataLakeClient` → `S3DataLakeClient`, `AzureDataLakeClient` (list, get, delete file operations)
- `AbstractDataLakeClientResource` → typed `ConfigurableResource` wrappers for Dagster DI
- `AbstractDataLakeFileSystemResource` → `s3fs`/`adlfs` wrappers for streaming reads

**Source connectors**:

- `SharePointResource` — MS Graph API. Config: `target_folders`, `exclude_folders`, `supported_filetypes`.
- `RcloneResource` — Rclone RC API. Config: `source_remote`, `include_patterns`, `exclude_patterns`. Wraps
  `RcloneClient` (async httpx/aiohttp). Supports 70+ cloud backends.
- `LocalFileSystemResource` — Pattern-based directory scanner. Config: `base_path`, include/exclude patterns (regex).

**Document processing**:

- `DocumentParserResource` — Selects parser by filetype. `LoaderType.MINERU` (default) or `DOCUMENT_INTELLIGENCE`.
  Fallbacks: `EpubReader`, `IPYNBReader`, `RawLoader`, `RTFReader`, `ImageLoader`.
- `MarkdownStructuralNodeParserResource` — LlamaIndex MD structural parser for chunking.
- `RecursiveSummaryParserResource` — Hierarchical summary generation for multi-level RAG.
- `TableRefinementResource` — LLM-powered table detection and structure splitting.

**LLM/Embedding**: `EmbeddingModelResource` (wraps `EmbeddingModelConfig`), `LanguageModelResource` (wraps `LLMConfig`).
Both use LiteLLM model names.

**Storage**: `MongoDocumentStoreResource` (LlamaIndex `MongoDocumentStore`), `MilvusVectorStoreResource` (uri,
collection_name, dimensions, index_type: HNSW or IVF_FLAT).

**Resource factory** (`resources/factory.py`) — assembles resource dicts for `Definitions`:

- `s3_data_lake_resources(container_name)` — client, file_system, io_manager, resource
- `mongo_document_store_resource(store_name)` — doc_store, io_manager, resource
- `milvus_vector_store_resource(uri, collection_name, dimensions)` — vector_store, io_manager
- `default_io_manager_s3_datalake_resources(container_name)` — Dagster PickleIOManager for inter-op data
- `local_mongo_milvus_storage_context_resource(vector_store_uri, store_name)` — combined MongoDB + Milvus

## Observable Assets & Dynamic Partitions

Observable assets monitor external sources. Return `DataVersionsByPartition` to signal which partitions changed:

```python
@observable_source_asset(key=key, partitions_def=partitions, io_manager_key="source_io_manager")
def observe_source(context, client: ResourceParam[SourceResource]) -> DataVersionsByPartition:
    files = client.fetch_minimal_files()
    return data_version_by_partition(context, files, partitions, max_partitions)
```

**DataVersion format**: `"{updated}-{hash}"` — detects both timestamp and content changes.

**Dynamic partitions**: Partition key = file URI (Stage 2) or file path (Stage 1). Managed via
`replace_partition_keys(context, partition_name, keys, max_partitions)` in `util/partition_utils.py`. Default max: 1000
partitions added/deleted per tick.

## Automation & Triggering

Three triggering mechanisms work together:

- **Eager automation**: `AutomationCondition.eager()` on downstream assets — materialize immediately when upstream
  changes. Enabled by `default_automation_sensor(assets, minimum_interval_seconds=60)`.
- **NATS sensor**: `nats_document_uploaded_sensor` — polls JetStream for `SourceUpdatedEvent` via
  `PipelineInstanceTopicManager`. Triggers observe job when documents are uploaded externally (e.g., via API).
- **Daily schedules**: `daily_schedule_at(job, hour, minute)` — cron-based observation for sources that don't push
  events.

## Playground

- `playground/__init__.py` — Full RAG pipeline using `default_definitions()` with playground bucket
- `playground/quick_start/simple_pipeline.py` — Hello-world: 2 basic assets, no external deps
- `playground/quick_start/my_document_pipeline.py` — Complete pipeline with all factories, resources, sensors

Start: `make playground` or `uv run dagster dev -m playground` Access: http://localhost:3000 (Dagster UI)

## Templates

`templates/sources/` — 7 pre-configured source templates. Each contains `.env.template` (required configuration),
`pipeline.py` (ready-to-use Dagster definition), and `README.md` (step-by-step setup guide).

Available: SharePoint, OneDrive, S3, Azure Blob, Google Drive, SFTP, Local FS.

Usage: Copy `.env.template` variables to your `.env`, follow the `README.md`, copy `pipeline.py` to your pipeline
location, customize. See `templates/sources/README.md` for the full guide including namespace configuration.

## App Entry Points

`app/` contains deployable Dagster gRPC code locations:

- `default_rag_pipeline/` — per-tenant bucket (`AIHubSettings().DEFAULT_BUCKET_NAME`)
- `shared_rag_pipeline/` — shared bucket (`AIHubSettings().SHARED_BUCKET_NAME`)

Each has a `Dockerfile` (Python 3.13-slim, uv, port 4000):
`dagster api grpc -h 0.0.0.0 -p 4000 -m "app.{pipeline_name}"`

## Testing

- pytest with pytest-asyncio
- Unit test ops: `build_op_context(resources={...})` → call op → assert
- Integration test assets: `materialize(assets=[...], resources={...}, partition_key="test")` → assert `result.success`
- Test markers: `slow`, `experimental`

## New Pipeline Checklist

1. Choose approach: `default_definitions()` for Stage 2 only, or add Stage 1 source definition builder
2. For new source: create observable factory + source I/O manager + source resource in `resources/`
3. For custom processing: create ops in `ops/`, compose into `@graph_asset` factory in `assets/factories/`
4. Wire into `Definitions` with resources, sensors, jobs, schedules
5. Test in playground: `make playground` → materialize in Dagster UI at http://localhost:3000
6. Deploy: create `app/{pipeline_name}/` with `__init__.py` + `Dockerfile`
7. Run `make test`

## Essential Files

**Core Entry Points**:

- Definition builders: `aihub_pipeline/util/definitions_util.py`
- Resource factories: `aihub_pipeline/resources/factory.py`

**Asset Factories**:

- Stage 2: `aihub_pipeline/assets/factories/data_lake_to_vector_store/`
- Stage 1 generic: `aihub_pipeline/assets/factories/source_to_data_lake/`
- SharePoint: `aihub_pipeline/assets/factories/share_point_to_data_lake/`
- Rclone: `aihub_pipeline/assets/factories/rclone_to_data_lake/`
- Local FS: `aihub_pipeline/assets/factories/local_files_system_to_data_lake/`

**I/O Managers**: `aihub_pipeline/io/` — S3DataLakeIOManager, AzureDataLakeIOManager, DocStoreIOManager,
VectorStoreIOManager, SharePointIOManager, RcloneIOManager, LocalFileSystemIOManager

**Domain Types**: `aihub_pipeline/types/` — DataLakeFile, RefDocDocument, SourceFile, SharePointFile, RcloneFile

**Resources**: `aihub_pipeline/resources/` — data_lake/ (base, s3, azure), parser/, vector_store/, doc_store/, llm/,
share_point/, rclone/, local_file_system/

**Sensors**: `aihub_pipeline/sensors/nats/nats_document_uploaded_sensor.py`

**Utilities**: `aihub_pipeline/util/` — definitions_util, id_utils, partition_utils, bucket_utils, key_utils

**App**: `app/default_rag_pipeline/__init__.py`, `app/shared_rag_pipeline/__init__.py`

**Playground**: `playground/__init__.py`, `playground/quick_start/`

**Templates**: `templates/sources/` — 7 source templates with README, .env.template, pipeline.py
