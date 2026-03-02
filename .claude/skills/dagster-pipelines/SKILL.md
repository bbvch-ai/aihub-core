---
name: dagster-pipelines
description: "Comprehensive reference for Dagster pipelines: asset factories, ops patterns, resources, IO managers, sensors, partitions, automation conditions, and the two-stage pipeline architecture. Use when user says 'how do pipelines work', 'create a new asset', 'add a resource', 'IO manager', 'configure a sensor', 'pipeline architecture', 'observable asset', 'partition setup', 'dagster definitions', 'asset factory', 'automation condition', or 'two-stage pipeline'. Do NOT use for scaffolding new pipelines (use scaffold-pipeline), debugging failed pipelines (use debug-pipeline), or rclone-specific setup (use rclone-guide)."
arguments:
  - name: topic
    description: Topic or question (e.g., "asset factory", "resources", "IO managers", "partitions", "sensors", "observable assets", "definitions factory")
allowed-tools: Read, Grep, Glob
---

# Dagster Pipelines — Comprehensive Reference

Look up Dagster pipeline information. Topic or question via `$ARGUMENTS`.

For architecture overview, folder structure, and domain types, see `aihub_pipeline/CLAUDE.md` (loaded automatically when
working in the pipeline scope).

______________________________________________________________________

## Architecture Quick Reference

| Concept               | Pattern                       | Purpose                                                   |
| --------------------- | ----------------------------- | --------------------------------------------------------- |
| **Assets**            | `@graph_asset`                | Concrete data artifacts (documents, nodes, embeddings)    |
| **Observable Assets** | `@observable_source_asset`    | Monitor external sources for changes                      |
| **Ops**               | `@op`                         | Individual processing steps composed WITHIN graph assets  |
| **Resources**         | `ConfigurableResource`        | External dependencies (LLM, storage, parsers)             |
| **IO Managers**       | `ConfigurableIOManager`       | Handle asset storage/retrieval per storage system         |
| **Jobs**              | `define_asset_job`            | Trigger observation or cleanup (NOT traditional op-based) |
| **Sensors**           | `@sensor`                     | Event-driven triggers (NATS, automation)                  |
| **Schedules**         | `ScheduleDefinition`          | Time-based triggers (daily observation)                   |
| **Partitions**        | `DynamicPartitionsDefinition` | Each document = separate partition                        |

**Key Rule**: Everything is asset-centric. Jobs exist only to trigger observation or cleanup. Ops exist only inside
graph assets. Never create standalone job-based pipelines.

______________________________________________________________________

## Definitions Factory Pattern

The `aihub_pipeline/aihub_pipeline/util/definitions_util.py` provides factory functions that assemble complete
`Definitions` objects with all assets, resources, sensors, jobs, and schedules wired together.

### `default_definitions()` — Stage 2 (DataLake to Vector Store)

```python
from aihub_pipeline.util.definitions_util import default_definitions

defs = default_definitions(
    datalake_container_name="my-bucket",          # S3 bucket name
    embedding_model_name="embedding/large",       # LiteLLM model
    llm_model_name="text-generation/mini",        # LiteLLM model
    with_summary_nodes=True,                      # Hierarchical RAG
    with_table_refinement=True,                   # LLM table structure detection
    with_figure_descriptions=True,                # Vision LLM figure descriptions
    auto_sync=False,                              # True if auto-synced via local FS
    observe_job_hour=2,                           # Daily observation at 2 AM
    observe_job_minute=0,
    remove_job_hour=3,                            # Daily cleanup at 3 AM
    remove_job_minute=0,
    vector_store_dimensions=None,                 # None = use MilvusSettings default
    max_partitions=1000,                          # Max partitions per operation
    document_parser_loader_type=LoaderType.MINERU,    # MinerU (default) or Azure Doc Intelligence
)
```

### `default_sharepoint_to_datalake_definitions()` — Stage 1 (SharePoint to S3)

```python
from aihub_pipeline.util.definitions_util import default_sharepoint_to_datalake_definitions

defs = default_sharepoint_to_datalake_definitions(
    datalake_container_name="sharepoint-docs",
    target_folders=["/Shared Documents/Sales"],
    exclude_folders=["/Shared Documents/Archive"],
    supported_filetypes=[".pdf", ".docx", ".pptx"],
    observe_job_hour=0,
    remove_job_hour=1,
)
```

### `default_local_filesystem_to_datalake_definitions()` — Stage 1 (Local FS to S3)

```python
from aihub_pipeline.util.definitions_util import default_local_filesystem_to_datalake_definitions

defs = default_local_filesystem_to_datalake_definitions(
    datalake_container_name="local-docs",
    base_path="/data/shared/documents",
    include_patterns=[r".*\.(pdf|docx|md)$"],    # Regex patterns
    exclude_patterns=[r".*/archive/.*"],
    observe_job_hour=0,
    remove_job_hour=1,
)
```

### `default_rclone_to_datalake_definitions()` — Stage 1 (Rclone to S3)

```python
from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

defs = default_rclone_to_datalake_definitions(
    datalake_container_name="onedrive-docs",
    source_remote="onedrive:Documents",           # Any rclone remote
    include_patterns=["*.pdf", "*.docx"],         # Rclone glob syntax
    exclude_patterns=["**/archive/**"],
    observe_job_hour=0,
    remove_job_hour=1,
)
```

______________________________________________________________________

## Asset Factory Pattern

All assets are created via **factory functions** that return parameterized `@graph_asset` or `@observable_source_asset`
definitions. Factories live in `aihub_pipeline/aihub_pipeline/assets/factories/`.

### Graph Asset Factory

```python
from dagster import AssetIn, AssetKey, AutomationCondition, DynamicPartitionsDefinition, Output, graph_asset

def documents_factory(
    key: AssetKey,
    data_lake_key: str | AssetKey,
    partitions: DynamicPartitionsDefinition,
    enable_table_refinement: bool,
    enable_figure_descriptions: bool,
) -> graph_asset:

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        ins={"data_lake_file": AssetIn(key=data_lake_key)},
        partitions_def=partitions,
        automation_condition=AutomationCondition.eager(),
        description="Create RefDocs from data lake files",
    )
    def document(data_lake_file: DataLakeFile) -> Output[RefDocDocument]:
        parsed = parse_document_from_data_lake(data_lake_file)
        if enable_figure_descriptions:
            parsed = generate_figure_descriptions(parsed)
        if enable_table_refinement:
            parsed = refine_document_tables(parsed)
        validated = ensure_refdoc_default_metadata(parsed)
        return insert_ref_doc_into_docstore(validated)

    return document
```

**Key characteristics**:

- `automation_condition=AutomationCondition.eager()` — auto-materialize when upstream changes
- `partitions_def` — dynamic partitions (1 document = 1 partition)
- `group_name` — logical grouping in Dagster UI
- `ins` — explicit upstream dependencies via `AssetIn`

### Observable Source Asset Factory

```python
from dagster import AssetKey, DataVersionsByPartition, DynamicPartitionsDefinition, observable_source_asset

def observable_data_lake_factory(
    key: AssetKey,
    partitions: DynamicPartitionsDefinition,
    max_partitions: int,
) -> observable_source_asset:

    @observable_source_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        partitions_def=partitions,
        io_manager_key="data_lake_io_manager",
        description="Observes the data lake for any changes",
    )
    def observable_data_lake(
        context: OpExecutionContext,
        data_lake_client: ResourceParam[AbstractDataLakeClient],
    ) -> DataVersionsByPartition:
        data_lake_files = fetch_all_files_in_data_lake_no_op(data_lake_client=data_lake_client)
        return data_version_by_partition_for_data_lake_files_no_op(
            context=context, asset_key=key, partition=partitions,
            data_lake_files=data_lake_files, max_partitions=max_partitions,
        )

    return observable_data_lake
```

**Key characteristics**:

- Returns `DataVersionsByPartition` (content hash per partition)
- Content hash change triggers downstream rematerialization
- `io_manager_key` — controls how partition data is loaded by downstream assets

______________________________________________________________________

## Ops Pattern

Ops are individual processing steps composed WITHIN graph assets.

### Basic Op

```python
from dagster import op, ResourceParam

@op(code_version="v1")
def parse_document_from_data_lake(
    data_lake_file: DataLakeFile,
    document_parser: ResourceParam[DocumentParserResource],
    data_lake_file_system: ResourceParam[AbstractFileSystem],
) -> RefDocDocument:
    reader = document_parser.get_document_parser_for_filetype(data_lake_file.filetype)
    documents = reader.load_data(data_lake_file.uri, fs=data_lake_file_system)
    ref_doc = RefDocDocument(**documents[0].model_dump())
    ref_doc.add_metadata_from_data_lake_file(data_lake_file)
    return ref_doc
```

### Op with Retry Policy

```python
from dagster import Backoff, RetryPolicy, op

@op(
    code_version="v1",
    retry_policy=RetryPolicy(max_retries=6, delay=1, backoff=Backoff.EXPONENTIAL),
)
def embed_nodes(
    nodes: list[TextNode],
    embedding_model: ResourceParam[BaseEmbedding],
) -> list[TextNode]:
    texts = [node.get_content(metadata_mode=MetadataMode.EMBED) for node in nodes]
    embeddings = embedding_model.get_text_embedding_batch(texts)
    for node, embedding in zip(nodes, embeddings):
        node.embedding = embedding
    return nodes
```

### Op Conventions

- `code_version` — change detection (bump when logic changes)
- `ResourceParam[T]` — resource injection (NOT `context.resources`)
- Typed inputs/outputs
- Keep ops focused and small
- Resources injected via `ResourceParam`, not `required_resource_keys`

______________________________________________________________________

## Resources

Resources are external dependencies injected into ops. All use Dagster's `ConfigurableResource` (Pydantic-based).

| Resource                               | Purpose                         | Key                        |
| -------------------------------------- | ------------------------------- | -------------------------- |
| `DocumentParserResource`               | MinerU / Azure Doc Intelligence | `document_parser`          |
| `MarkdownStructuralNodeParserResource` | Structural chunking             | `node_parser`              |
| `RecursiveSummaryParserResource`       | Hierarchical summaries          | `summary_parser`           |
| `TableRefinementResource`              | LLM table refinement            | `table_refinement`         |
| `EmbeddingModelResource`               | LiteLLM embeddings              | `embedding_model`          |
| `LanguageModelResource`                | LiteLLM text generation         | `language_model`           |
| `S3DataLakeClientResource`             | S3/MinIO client                 | `data_lake_client`         |
| `S3DataLakeFileSystemResource`         | S3 filesystem (s3fs)            | `data_lake_file_system`    |
| `AzureDataLakeClientResource`          | Azure ADLS client               | `data_lake_client`         |
| `MongoDocumentStoreResource`           | MongoDB doc store               | `doc_store`                |
| `MilvusVectorStoreResource`            | Milvus vector store             | `vector_store`             |
| `SharePointResource`                   | SharePoint connector            | `share_point_client`       |
| `LocalFileSystemResource`              | Local/network FS                | `local_file_system_client` |
| `RcloneResource`                       | Universal cloud storage         | `rclone_client`            |
| `DataLakeResource`                     | Container/directory config      | `data_lake_resource`       |
| `DocStoreResource`                     | Doc store name config           | `doc_store_resource`       |

### Resource Factory Pattern

```python
# aihub_pipeline/aihub_pipeline/resources/factory.py

def s3_data_lake_resources(container_name, directory_name=None) -> dict:
    data_lake_client = S3DataLakeClientResource(container_name=container_name)
    data_lake_file_system = S3DataLakeFileSystemResource()
    data_lake_io_manager = S3DataLakeIOManager(
        data_lake_client=data_lake_client,
        data_lake_file_system=data_lake_file_system,
    )
    return {
        "data_lake_client": data_lake_client,
        "data_lake_file_system": data_lake_file_system,
        "data_lake_io_manager": data_lake_io_manager,
        "data_lake_resource": DataLakeResource(container_name=container_name, directory_name=directory_name),
    }

def local_mongo_milvus_storage_context_resource(vector_store_uri, store_name, dimensions) -> dict:
    return {
        **mongo_document_store_resource(document_store_name=store_name),
        **milvus_vector_store_resource(
            vector_store_uri=vector_store_uri, vector_store_name=store_name, dimensions=dimensions
        ),
    }
```

### Settings Integration

Resources read connection details from `aihub_lib` settings (Pydantic `BaseSettings`):

| Settings Class                      | Env Prefix                     | Purpose                |
| ----------------------------------- | ------------------------------ | ---------------------- |
| `S3StorageSettings`                 | `S3_`                          | S3/MinIO connection    |
| `MilvusSettings`                    | `MILVUS_`                      | Milvus vector DB       |
| `RcloneSettings`                    | `RCLONE_`                      | Rclone RC API          |
| `MineruSettings`                    | `MINERU_`                      | MinerU parser          |
| `AzureDocumentIntelligenceSettings` | `AZURE_DOCUMENT_INTELLIGENCE_` | Azure Doc Intelligence |

______________________________________________________________________

## IO Managers

IO managers control how assets are stored and retrieved. Each storage system has a dedicated IO manager in
`aihub_pipeline/aihub_pipeline/io/`.

| IO Manager                 | Key                            | Storage      | Direction     | Partition Behavior              |
| -------------------------- | ------------------------------ | ------------ | ------------- | ------------------------------- |
| `S3DataLakeIOManager`      | `data_lake_io_manager`         | S3/MinIO     | Read + Write  | Partition key = file URI        |
| `AzureDataLakeIOManager`   | `data_lake_io_manager`         | Azure ADLS   | Read + Write  | Partition key = file URI        |
| `DocStoreIOManager`        | `doc_store_io_manager`         | MongoDB      | Read + Write  | Partition key = document URI/ID |
| `VectorStoreIOManager`     | `vector_store_io_manager`      | Milvus       | Read + Write  | Partition key = document URI/ID |
| `SharePointIOManager`      | `sharepoint_io_manager`        | SharePoint   | **Read-only** | Partition key = SP file path    |
| `LocalFileSystemIOManager` | `local_file_system_io_manager` | Local FS     | **Read-only** | Partition key = file path       |
| `RcloneIOManager`          | `rclone_io_manager`            | Rclone (70+) | **Read-only** | Partition key = file path       |
| `S3PickleIOManager`        | `io_manager` (default)         | S3/MinIO     | Read + Write  | Pickled Python objects          |

**Read-only IO managers**: Source connectors (SharePoint, LocalFS, Rclone) never write back to sources.

### Partitioned vs Non-Partitioned Loading

```python
def load_input(self, context: InputContext):
    if context.has_partition_key:
        # Single partition — load one document
        return self._load_single(context.partition_key)
    else:
        # No partition — load ALL partitions (for cleanup/aggregation)
        all_keys = partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
        return [self._load_single(k) for k in all_keys]
```

### VectorStoreIOManager Retry Logic

Milvus has eventual consistency — nodes may not be immediately queryable after insertion:

```python
max_retry_time = 30  # seconds
retry_interval = 1   # second

while datetime.now() < end_time:
    nodes = vector_store.get_nodes(filters=filters)
    if nodes:
        return nodes
    time.sleep(retry_interval)
```

______________________________________________________________________

## Dynamic Partitions

Every pipeline uses **dynamic partitions** — each document becomes a separate partition.

```python
from dagster import DynamicPartitionsDefinition

document_partitions = DynamicPartitionsDefinition(
    name=f"{datalake_container_name}_document_partitions"
)
```

### Partition Management

```python
# aihub_pipeline/aihub_pipeline/util/partition_utils.py

def replace_partition_keys(context, partition_name, keys, max_partitions):
    existing = set(context.instance.get_dynamic_partitions(partition_name))
    incoming = set(keys)

    to_add = incoming - existing
    to_delete = existing - incoming

    for key in list(to_add)[:max_partitions]:
        context.instance.add_dynamic_partitions(partition_name, [key])

    for key in list(to_delete)[:max_partitions]:
        context.instance.delete_dynamic_partition(partition_name, key)
```

**Partition key = document URI** (e.g., `s3://bucket/path/to/doc.pdf`).

### DataVersionsByPartition

Observable assets return content hashes per partition to trigger downstream:

```python
from dagster import DataVersionsByPartition

return DataVersionsByPartition({
    "s3://bucket/doc1.pdf": "abc123hash",
    "s3://bucket/doc2.pdf": "def456hash",
})
```

Version change triggers downstream assets with `AutomationCondition.eager()` to auto-materialize.

______________________________________________________________________

## Automation Conditions

### Eager Automation (Default)

```python
from dagster import AutomationCondition

@graph_asset(
    automation_condition=AutomationCondition.eager(),
)
def my_asset(...):
    # Auto-materializes when ANY upstream dependency changes
    pass
```

### Custom: All Dependencies Completed

```python
# aihub_pipeline/aihub_pipeline/automation/all_deps_completed.py
from dagster import AutomationCondition

all_deps_completed = (
    ~AutomationCondition.any_deps_missing()
    & ~AutomationCondition.any_deps_in_progress()
)
```

### Automation Sensor (Required)

Automation conditions require a sensor to evaluate them. Include in every `Definitions`:

```python
from dagster import AutomationConditionSensorDefinition, DefaultSensorStatus

def default_automation_sensor(assets, minimum_interval_seconds=60):
    return AutomationConditionSensorDefinition(
        "AutomaterializeSensor",
        target=assets,
        default_status=DefaultSensorStatus.RUNNING,
        minimum_interval_seconds=minimum_interval_seconds,
    )
```

______________________________________________________________________

## Sensors, Schedules, and Jobs

### NATS Document Uploaded Sensor

Polls NATS JetStream for `SourceUpdatedEvent` to trigger pipeline runs:

```python
from aihub_pipeline.sensors.nats.nats_document_uploaded_sensor import nats_document_uploaded_sensor

sensor = nats_document_uploaded_sensor(
    job=observe_job,
    topic_manager=PipelineInstanceTopicManager(
        source_type=INTERNAL_DATALAKE,          # "datalake"
        source_id=datalake_container_name,
        target_type=INTERNAL_KNOWLEDGE_DB,      # "knowledge"
        target_id=store_name,
    ),
)
```

**Flow**: Document uploaded via API sends `SourceUpdatedEvent` to NATS. Sensor triggers `observe_job`. Observable asset
detects new partition. Downstream assets with `AutomationCondition.eager()` auto-materialize.

### Schedules

Time-based triggers (use sparingly — prefer observable assets + automation conditions):

```python
from aihub_pipeline.schedules.factory import daily_schedule_at

schedules=[
    daily_schedule_at(observe_job, hour=2, minute=0),   # Observe at 2 AM
    daily_schedule_at(remove_job, hour=3, minute=0),    # Cleanup at 3 AM
]
```

Timezone: `Europe/Berlin`. Default status: `RUNNING`.

### Jobs

Jobs wrap asset selections for triggering via sensors/schedules:

```python
from aihub_pipeline.jobs.factory import observe_source_job, materialize_asset_job

# Observation job (discovers new/changed partitions)
observe_job = observe_source_job(
    observable_asset=my_observable_asset,
    source_location_name="my-bucket",
)

# Materialization job (e.g., cleanup)
remove_job = materialize_asset_job(
    source_location_name="my-bucket",
    job_name="remove_documents",
    asset_selection=AssetSelection.keys(removed_documents_key),
)
```

______________________________________________________________________

## Metadata and Tags

### Output Metadata

```python
context.add_output_metadata({
    "items_processed": len(data),
    "processing_time": result.time,
})
```

### Asset Materialization Metadata (Observable Assets)

```python
context.instance.report_runless_asset_event(
    AssetMaterialization(
        asset_key=asset_key,
        partition=partition_key,
        metadata={
            "Number of Files": len(files),
            "Total File Size (MB)": total_size / 1e6,
        },
    )
)
```

### Git Code References

```python
from dagster import link_code_references_to_git, with_source_code_references

assets = link_code_references_to_git(
    assets_defs=with_source_code_references(assets),
    git_url="https://github.com/bbvch-ai/aihub-core",
    git_branch="main",
)
```

______________________________________________________________________

## Conventions Checklist

- [ ] Assets use factory functions (never define assets inline in definitions)
- [ ] Graph assets compose ops (ops are not standalone)
- [ ] Observable assets return `DataVersionsByPartition` (not raw data)
- [ ] All downstream assets use `AutomationCondition.eager()` for reactive processing
- [ ] Dynamic partitions: partition key = document URI
- [ ] Resources inherit from `ConfigurableResource` (Pydantic-based)
- [ ] IO managers inherit from `ConfigurableIOManager`
- [ ] Source connectors are read-only (IO managers raise `NotImplementedError` on `handle_output`)
- [ ] Automation condition sensor included in all `Definitions`
- [ ] Jobs wrap `AssetSelection` (not standalone op graphs)
- [ ] Ops use `ResourceParam[T]` for resource injection
- [ ] Ops include `code_version` for change detection
- [ ] Retry policies use `Backoff.EXPONENTIAL` for external calls
- [ ] Schedules use `Europe/Berlin` timezone
- [ ] `default_process_executor()` (in-process) used unless parallel processing needed
