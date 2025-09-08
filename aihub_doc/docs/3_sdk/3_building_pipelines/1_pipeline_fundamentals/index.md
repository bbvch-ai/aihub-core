---
title: Pipeline Fundamentals
index: 1
---

# Pipeline Fundamentals

This section covers the core components used in AI-Hub pipelines. 
Understanding these fundamentals is necessary for implementing document processing workflows using the `aihub_pipeline` library.

## Core architecture {#core-architecture}

AI-Hub pipelines are built on Dagster's asset-based architecture, where data processing is organized as a graph of interconnected assets that produce and consume typed data artifacts.

### Asset-based processing model {#asset-based-model}

Each processing step produces concrete, versioned data artifacts:

```python
@asset
def processed_documents(raw_documents: List[RawDocument]) -> List[ProcessedDocument]:
    """Asset that transforms raw documents into processed documents."""
    return [process_document(doc) for doc in raw_documents]
```

**Key characteristics:**
- **Materialization**: Each asset execution creates a concrete data artifact
- **Versioning**: Assets track data versions and dependencies
- **Lineage**: Automatic dependency tracking between assets
- **Incremental processing**: Assets only recompute when upstream dependencies change

## Component hierarchy {#component-hierarchy}

AI-Hub pipelines consist of these components:

```
Pipeline Definition (Definitions)
├── Assets (graph_asset, observable_source_asset)
│   ├── Operations (@op)
│   └── Asset Dependencies (AssetIn)
├── Resources (ConfigurableResource)
├── I/O Managers (ConfigurableIOManager)
├── Jobs (observe_source_job, materialize_asset_job)
├── Schedules (daily_schedule_at)
└── Sensors (default_automation_sensor)
```

## Assets {#assets}

Assets represent data artifacts produced by the pipeline. AI-Hub uses several asset types:

### Graph assets {#graph-assets}

Graph assets compose multiple operations into processing workflows:

```python
@graph_asset(
    key=AssetKey(["documents"]),
    partitions_def=document_partitions,
    automation_condition=AutomationCondition.eager(),
)
def documents(data_lake_file: DataLakeFile) -> RefDocDocument:
    """Multi-step document processing."""
    parsed = parse_document_from_data_lake(data_lake_file)
    enriched = ensure_refdoc_default_metadata(parsed)
    return insert_ref_doc_into_docstore(enriched)
```

### Observable source assets {#observable-assets}

Observable source assets monitor external systems for changes:

```python
@observable_source_asset(
    key=AssetKey(["data_lake"]),
    partitions_def=document_partitions,
)
def data_lake_observer(context: OpExecutionContext):
    """Observe data lake and create partitions for new/changed documents."""
    changed_files = scan_data_lake_for_changes()
    
    data_versions = {}
    for file_info in changed_files:
        partition_key = file_info.document_id
        data_version = DataVersion(file_info.modified_time.isoformat())
        data_versions[partition_key] = data_version
    
    return DataVersions(data_versions)
```

## Operations {#operations}

Operations are individual processing steps within graph assets:

```python
@op(
    required_resource_keys={"document_parser"},
    ins={"data_lake_file": In(DataLakeFile)},
    out=Out(RefDocDocument),
)
def parse_document_from_data_lake(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
) -> RefDocDocument:
    """Parse a single document from data lake file."""
    parser = context.resources.document_parser
    reader = parser.get_document_parser_for_filetype(data_lake_file.filetype)
    documents = reader.load_data(data_lake_file.uri)
    
    context.log.info(f"Parsed document: {data_lake_file.uri}")
    return RefDocDocument(**documents[0].model_dump())
```

## Resources {#resources}

Resources manage external dependencies and configuration:

```python
class DocumentParserResource(ConfigurableResource):
    """Configurable document parsing resource."""
    
    loader_type: LoaderType = LoaderType.DOCLING
    
    def get_document_parser_for_filetype(self, filetype: str) -> BaseReader:
        """Get parser instance for specific file type."""
        if self.loader_type == LoaderType.DOCLING:
            return DoclingReader()
        elif self.loader_type == LoaderType.DOCUMENT_INTELLIGENCE:
            return AzureDocIntelligenceReader()
        else:
            raise ValueError(f"Unsupported loader type: {self.loader_type}")
```

## I/O Managers {#io-managers}

I/O Managers control how data flows between assets. When an asset produces output, its I/O manager handles storage. When a downstream asset needs that data as input, the I/O manager retrieves it.

AI-Hub includes several specialized I/O managers:

### Document Store I/O Manager {#doc-store-io-manager}

Handles RefDoc documents using MongoDB storage:

```python
@asset(
    partitions_def=document_partitions,
    io_manager_key="doc_store_io_manager"
)
def documents(data_lake_file: DataLakeFile) -> RefDocDocument:
    """Asset that stores documents in document store."""
    return parse_document(data_lake_file)
    # DocStoreIOManager.handle_output() stores the RefDoc

@asset(partitions_def=document_partitions)
def nodes(ref_doc: RefDocDocument) -> List[TextNode]:
    """Asset that loads documents from document store."""
    # DocStoreIOManager.load_input() loads the RefDoc
    return chunk_document(ref_doc)
```

### Vector Store I/O Manager {#vector-store-io-manager}

Handles embedded nodes using vector storage:

```python
@asset(
    partitions_def=document_partitions,
    io_manager_key="vector_store_io_manager"
)
def embeddings(nodes: List[TextNode]) -> List[TextNode]:
    """Asset that stores embeddings in vector store."""
    return embed_nodes(nodes)
    # VectorStoreIOManager.handle_output() stores embedded nodes
```

### Data Lake I/O Manager {#data-lake-io-manager}

Handles file references and data lake operations:

```python
@asset(
    partitions_def=document_partitions,
    io_manager_key="data_lake_io_manager"
)
def processed_files(input_files: List[DataLakeFile]) -> List[DataLakeFile]:
    """Asset using data lake storage."""
    return process_files(input_files)
```

## Asset factories {#asset-factories}

Asset factories provide configurable, reusable asset definitions:

```python
def documents_factory(
    key: AssetKey,
    data_lake_key: AssetKey,
    partitions: DynamicPartitionsDefinition,
) -> graph_asset:
    """Factory for creating document processing assets."""
    
    @graph_asset(
        key=key,
        ins={"data_lake_file": AssetIn(key=data_lake_key)},
        partitions_def=partitions,
        automation_condition=AutomationCondition.eager(),
    )
    def documents(data_lake_file: DataLakeFile) -> RefDocDocument:
        parsed = parse_document_from_data_lake(data_lake_file)
        enriched = ensure_refdoc_default_metadata(parsed)
        return insert_ref_doc_into_docstore(enriched)
    
    return documents
```

Factories compose to create complete pipelines:

```python
def create_rag_pipeline(namespace: str, partitions: DynamicPartitionsDefinition):
    """Create complete RAG processing pipeline using factories."""
    data_lake_key = AssetKey([namespace, "data_lake"])
    documents_key = AssetKey([namespace, "documents"])
    nodes_key = AssetKey([namespace, "nodes"])
    
    return [
        observable_data_lake_factory(data_lake_key, partitions),
        documents_factory(documents_key, data_lake_key, partitions),
        nodes_factory(nodes_key, documents_key, partitions),
        summary_nodes_factory(
            key=AssetKey([namespace, "summary_nodes"]),
            document_key=documents_key,
            nodes_key=nodes_key,
            partitions=partitions
        ),
    ]
```

## Dynamic partitioning {#dynamic-partitioning}

Dynamic partitions are created at runtime based on discovered data:

```python
document_partitions = DynamicPartitionsDefinition(name="documents")

# Observable asset creates partitions when it detects new documents
@observable_source_asset(
    key=AssetKey(["data_lake"]),
    partitions_def=document_partitions,
)
def data_lake_observer(context):
    changed_files = scan_data_lake_for_changes()
    data_versions = {}
    
    for file_info in changed_files:
        partition_key = file_info.document_id
        data_versions[partition_key] = DataVersion(file_info.modified_time.isoformat())
    
    return DataVersions(data_versions)
```

Assets can be partitioned to process documents independently:

```python
@asset(
    partitions_def=document_partitions,
    automation_condition=AutomationCondition.eager(),
)
def process_document_partition(
    context: AssetExecutionContext,
    data_lake_file: DataLakeFile,
) -> RefDocDocument:
    """Process a single document partition."""
    partition_key = context.partition_key
    return process_single_document(data_lake_file, partition_key)
```

## Pipeline data types {#data-types}

AI-Hub pipelines use strongly-typed data structures:

| Type             | Purpose                      | Key Attributes                             |
|------------------|------------------------------|--------------------------------------------|
| `DataLakeFile`   | File reference in data lake  | `uri`, `filetype`, `modified_time`, `size` |
| `RefDocDocument` | Parsed document with content | `doc_id`, `text`, `metadata`, `images`     |
| `TextNode`       | Text chunk for processing    | `text`, `metadata`, `relationships`        |

## Jobs and schedules {#jobs-schedules}

### Jobs {#jobs}

AI-Hub provides factory functions for common job types:

```python
# Job for observing data sources
observe_job = observe_source_job(
    observable_asset=data_lake_observer,
    namespace_name="documents",
)

# Job for materializing specific assets
materialize_job = materialize_asset_job(
    namespace_name="documents",
    job_name="process_documents",
    asset_selection=AssetSelection.keys(documents_key, nodes_key),
)
```

### Schedules {#schedules}

Schedules trigger jobs at specified times:

```python
# Schedule observation job to run daily
observe_schedule = daily_schedule_at(
    job=observe_job,
    hour=2,  # Run at 2 AM daily
    minute=0,
)
```

### Automation sensor {#automation-sensor}

AI-Hub provides a default automation sensor for eager asset materialization:

```python
# Sensor enables eager automation for assets
automation_sensor = default_automation_sensor(
    assets=pipeline_assets,
)
```

## Resource configuration {#resource-configuration}

AI-Hub provides resource factory functions for common configurations:

### Local development resources {#local-resources}

```python
# Local MongoDB + Milvus setup
local_resources = {
    **local_mongo_milvus_storage_context_resource(
        vector_store_uri="http://localhost:19530",
        store_name="dev_store",
        namespace_name="development",
    ),
    **default_io_manager_s3_datalake_resources(
        container_name="dev-container",
        directory_name="documents"
    ),
    "document_parser": DocumentParserResource(
        loader_type=LoaderType.DOCLING,
    ),
}
```

### Cloud resources {#cloud-resources}

```python
# MongoDB + Azure AI Search setup
production_resources = {
    **mongo_aisearch_storage_context_resources(
        store_name="prod_store",
        namespace_name="production",
    ),
    "document_parser": DocumentParserResource(
        loader_type=LoaderType.DOCUMENT_INTELLIGENCE,
        timeout=300,
    ),
}
```

## Complete pipeline definition {#complete-pipeline}

All components combine in a Definitions object:

```python
def create_document_pipeline(namespace: str) -> Definitions:
    """Create complete document processing pipeline."""
    
    partitions = DynamicPartitionsDefinition(name=f"{namespace}_documents")
    assets = create_rag_pipeline(namespace, partitions)
    
    observe_job = observe_source_job(
        observable_asset=assets[0],  # Observable data lake asset
        namespace_name=namespace,
    )
    
    return Definitions(
        assets=assets,
        resources=local_mongo_milvus_storage_context_resource(
            vector_store_uri="http://localhost:19530",
            store_name="enterprise_kb",
            namespace_name=namespace,
        ),
        jobs=[observe_job],
        schedules=[daily_schedule_at(observe_job, hour=2, minute=0)],
        sensors=[default_automation_sensor(assets)],
    )
```

## Next sections {#next-sections}

The following sections provide implementation guidance building on these fundamentals:

- **[Data Ingestion Patterns](../2_data_ingestion_patterns/)** - Complete RAG pipeline implementation examples
- **[Observable Assets](../3_observable_assets/)** - Change-driven processing implementation  
- **[Job Scheduling](../4_job_scheduling/)** - Orchestration configuration
- **[Pipeline Observation](../5_pipeline_observation/)** - Monitoring and debugging