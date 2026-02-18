# aihub_pipeline - Data Ingestion & Processing

**Purpose**: Dagster-based pipelines for document ingestion, parsing, embedding generation, and vector storage. Prepares data for RAG agents.

Tech Stack & Paradigms: Dagster asset-based orchestration with dagster-webserver UI (localhost:3002). dagster-postgres for storage backend. dagster-azure for Azure cloud integration (ADLS). dagster-aws for AWS S3 integration. LlamaIndex readers for file ingestion. adlfs for Azure Data Lake. s3fs + boto3 for S3 access. matplotlib for visualizations. lxml for XML/HTML parsing. Observable assets with materialization tracking. I/O managers for storage. Dynamic partitioning. Sensors for event-driven triggers. Schedules for recurring jobs. Multi-asset definitions. Resource management. Structured metadata for lineage tracking. pytest for testing.

## Scope Responsibility

Observable data processing workflows. Document lifecycle: ingestion → parsing → chunking → embedding → vector storage. NOT agent logic (pipelines produce data for agents).

## Folder Structure

```
aihub_pipeline/
├── assets/factories/          # Asset factory functions
│   ├── data_lake_to_vector_store/    # DL → VS pipeline
│   └── share_point_to_data_lake/     # SP → DL pipeline
├── automation/                # Automation conditions & policies
├── executors/                 # Job execution configs
├── io/                        # I/O managers (CRITICAL)
│   ├── AzureDataLakeIOManager.py
│   ├── DocStoreIOManager.py
│   ├── SharePointIOManager.py
│   └── VectorStoreIOManager.py
├── ops/                       # Operations (data processing steps)
│   ├── data_lake/
│   ├── document/
│   ├── nodes/
│   └── share_point/
├── resources/                 # Resource definitions (LLM, parser, storage)
├── sensors/                   # Event-driven triggers
│   └── factory.py             # default_automation_sensor (auto-materialization)
├── schedules/                 # Time-based triggers
│   └── factory.py             # daily_schedule_at, default_daily_materialize_schedule
├── jobs/                      # Job definitions
└── playground/                # Working example (START HERE)
    └── __init__.py            # Complete pipeline demo
```

## Key Concepts

**Asset-Based Architecture** (NOT job-based):

- **Asset**: Concrete data artifact (file, document, node, embedding)
- **Materialization**: Producing an asset (runs computation)
- **Asset Factory**: Reusable function creating parameterized assets

**Observable Assets**:

- Monitor external sources (data lake, SharePoint) for changes
- Trigger runs only when new data detected (NOT on schedule)
- Dynamic partitions: Each document = separate partition

**Data Versions**:

- Each asset has version reflecting source state
- Version change → triggers downstream rematerialization
- Ensures traceability: Which data produced which agent response?

## Pipeline Architecture

**Two-Stage Split**: Source-specific ingestion, then unified processing.

**Stage 1 (Per-Source)**: `Enterprise Source` → `DataLakeFile`

- Multiple independent pipelines (SharePoint, S3, ADLS, filesystem, databases)
- Each source has dedicated connector (e.g., SharePointIOManager)
- Output: Unified DataLakeFile in S3-compatible storage

**Stage 2 (Unified)**: `DataLakeFile` → `RefDocDocument` → `TextNode[]`

- Single pipeline processes all data lake files regardless of origin
- Parsing (MinerU/MarkItDown) → Chunking (semantic/structural) → Embedding → Vector Store
- Storage: MongoDB (documents via DocStoreIOManager), Milvus (vectors via VectorStoreIOManager)

## Asset Factory Pattern

```python
def documents_factory(
    key: AssetKey,
    data_lake_key: AssetKey,
    partitions: DynamicPartitionsDefinition,
) -> graph_asset:
    @graph_asset(
        key=key,
        partitions_def=partitions,
        ins={"data_lake_file": AssetIn(key=data_lake_key)},
        automation_condition=AutomationCondition.eager(),
    )
    def documents(data_lake_file: DataLakeFile) -> RefDoc:
        return parse_document(data_lake_file)
    return documents
```

## Operations (Ops)

**Pattern**: `@op` with resource deps, typed inputs/outputs.

```python
@op(
    required_resource_keys={"document_parser"},
    ins={"file": In(DataLakeFile)},
    out=Out(RefDoc),
)
def parse_document(context, file: DataLakeFile) -> RefDoc:
    parser = context.resources.document_parser
    return parser.parse(file)
```

## Resources

**Purpose**: External dependencies (parsers, LLMs, storage). Injected into ops via `context.resources`.

**Types**:

- **DocumentParser**: MinerU, MarkItDown, PDF, Markdown parsers
- **LLM/Embedding**: Azure OpenAI, OpenAI, Hugging Face
- **Storage**: Milvus (primary vector store), MongoDB, Data Lake

**Pattern**: `ConfigurableResource` subclass.

## I/O Managers

**Purpose**: Handle asset storage/retrieval. Map asset keys to storage systems.

**Examples**:

- `DocStoreIOManager`: MongoDB (RefDocs)
- `VectorStoreIOManager`: Milvus (embeddings)
- `AzureDataLakeIOManager`: ADLS (raw files)

**Custom I/O Manager**:

```python
class MyIOManager(ConfigurableIOManager):
    def handle_output(self, context, obj):
        # Store asset
        pass

    def load_input(self, context):
        # Retrieve asset
        pass
```

## Automation & Scheduling

**Eager Automation**: `AutomationCondition.eager()` materializes immediately when upstream changes.

**Sensors**: Trigger runs based on external events (file uploads, API callbacks).

**Schedules**: Time-based runs (use sparingly; prefer observable assets).

## Development Workflow

1. **Create ops**: Define processing steps in `ops/`
2. **Create resources**: Define deps in `resources/`
3. **Create asset factory**: Compose ops into assets in `assets/factories/`
4. **Test**: Unit test ops, integration test assets
5. **Run Dagster UI**: `make playground` or `poetry run dagster dev -m playground`
6. **Observe**: http://localhost:3000 (asset lineage, run logs, errors)

## Testing

**Unit Test Ops**:

```python
from dagster import build_op_context

context = build_op_context(resources={"my_resource": MyResource()})
result = my_op(context, input_data)
assert result.processed
```

**Integration Test Assets**:

```python
from dagster import materialize

result = materialize(
    assets=[my_asset],
    partition_key="test_partition",
    resources={"my_resource": MyResource()},
)
assert result.success
```

## Playground

**Location**: `/home/user/aihub-core/aihub_pipeline/playground/`
**Start**: `make playground` (or `poetry run dagster dev -m playground`)
**Access**: http://localhost:3000 (Dagster UI)

## Pre-Commit

```bash
make pr-ready  # Format + lint
make test      # Run tests
```

## Essential Files

- Playground: `/home/user/aihub-core/aihub_pipeline/playground/__init__.py`
- Asset factories: `/home/user/aihub-core/aihub_pipeline/aihub_pipeline/assets/factories/`
- I/O managers: `/home/user/aihub-core/aihub_pipeline/aihub_pipeline/io/`
- Resources: `/home/user/aihub-core/aihub_pipeline/aihub_pipeline/resources/`
- Ops: `/home/user/aihub-core/aihub_pipeline/aihub_pipeline/ops/`

## Quick Reference

**Create pipeline**:

1. Define ops in `ops/my_domain/`
2. Define resources in `resources/my_domain/`
3. Create asset factory in `assets/factories/my_domain/`
4. Instantiate in playground: `my_asset_factory(key=AssetKey(["my_asset"]), ...)`
5. Run: `make playground`, materialize in UI

**Observable pattern**:

```python
@observable_source_asset(key=AssetKey(["source"]), partitions_def=partitions)
def source_observer(context):
    # Check external source for changes
    # Return DataVersion for each partition
    pass
```

**Logging**: `context.log.info()`, `context.add_output_metadata()`
