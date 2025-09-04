---
title: "Pipeline Fundamentals"
index: 1
---
[WIP]

# Pipeline Fundamentals

Understanding the core architecture and concepts of AI-Hub pipelines is essential before building your own data processing workflows. This section covers the foundational patterns and terminology you need to work effectively with the `aihub_pipeline` library.

## Architecture overview {#architecture}

> [!NOTE]
> AI-Hub pipelines are built using Dagster's asset-based approach, where each processing step produces concrete, versioned data artifacts.

This provides several advantages over traditional ETL pipelines:

::: tip Asset-Based Benefits
- **Materialized assets**: Every processing stage creates tangible data you can inspect and debug
- **Automatic lineage**: Dependencies between assets create clear data flow visualization
- **Incremental processing**: Only reprocess data when upstream dependencies change
- **Built-in observability**: Monitor execution progress and investigate failures
:::

## Core components {#core-components}

### Assets and asset factories {#assets-factories}

**Assets** represent data objects produced by your pipeline. Instead of defining assets directly, use **asset factories** to create configurable, reusable definitions:

::: code-group

```python [Asset Factory Definition]
def documents_factory(
    key: AssetKey,
    data_lake_key: AssetKey, 
    partitions: DynamicPartitionsDefinition
) -> graph_asset:
    """Factory for creating document processing assets."""
    
    @graph_asset(
        key=key,
        ins={"data_lake_file": AssetIn(key=data_lake_key)},
        partitions_def=partitions,
        automation_condition=AutomationCondition.eager(),
    )
    def documents(data_lake_file: DataLakeFile) -> RefDocDocument:
        return insert_ref_doc_into_docstore(
            ensure_refdoc_default_metadata(
                parse_document_from_data_lake(data_lake_file)
            )
        )
    
    return documents
```

```python [Asset Factory Usage]
# Create document processing asset
document_asset = documents_factory(
    key=AssetKey(["production", "documents"]),
    data_lake_key=AssetKey(["production", "data_lake"]),
    partitions=DynamicPartitionsDefinition(name="doc_partitions"),
)

# Use in pipeline definition
assets = [
    observable_data_lake_factory(DATA_LAKE_KEY, partitions),
    document_asset,
    nodes_factory(NODES_KEY, DOCUMENT_KEY, partitions),
]
```

:::

### Operations (ops) {#operations}

**Operations** are the individual processing steps that transform data. They specify inputs, outputs, and required resources:

::: details Operation Implementation
```python
@op(
    required_resource_keys={"document_parser"},
    ins={"data_lake_file": In(DataLakeFile)},
    out=Out(RefDocDocument),
)
def parse_document_from_data_lake(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
    document_parser: DocumentParserResource,
) -> RefDocDocument:
    """Parse document from data lake file."""
    reader = document_parser.get_document_parser_for_filetype(data_lake_file.filetype)
    documents = reader.load_data(data_lake_file.uri)
    return RefDocDocument(**documents[0].model_dump())
```
:::

### Resources {#resources}

**Resources** manage external dependencies and configurations that operations need:

::: code-group

```python [Resource Definition]
class DocumentParserResource(ConfigurableResource):
    """Resource for configuring document parsing."""
    
    loader_type: LoaderType = LoaderType.DOCLING
    
    def get_document_parser_for_filetype(self, filetype: str) -> BaseReader:
        """Get appropriate parser for file type."""
        # Implementation logic here
        pass
```

```python [Resource Usage]
# Configure resources for different environments
resources = {
    "document_parser": DocumentParserResource(
        loader_type=LoaderType.DOCLING
    ),
    "vector_store": VectorStoreResource(
        connection_string="mongodb://localhost:27017"
    ),
    "embedding_model": EmbeddingModelResource(
        embedding_config=EmbeddingModelConfig(
            model_name="azure/text-embedding-3-large"
        )
    ),
}
```

:::

## Data types and flow {#data-types}

### Pipeline data types {#pipeline-types}

> [!NOTE]
> The pipeline uses strongly-typed data structures to ensure reliability throughout the **data lake to vector store** processing flow.

| Type | Purpose | Key Attributes |
|------|---------|---------------|
| **`DataLakeFile`** | File in data lake with metadata | `uri`, `filetype`, `modified_time`, `size` |
| **`RefDocDocument`** | Parsed document with content | `doc_id`, `text`, `metadata`, `images` |
| **`TextNode`** | Text chunk for embedding | `text`, `metadata`, `embedding` |
| **Custom types** | Domain-specific structures | Defined per use case |

### Core data flow: Data lake to vector store {#data-flow}

> [!IMPORTANT]
> The standard AI-Hub pipeline follows the **data lake to vector store** pattern, optimized for RAG agent knowledge retrieval.

```mermaid
graph LR
    A[DataLakeFile] --> B[RefDocDocument] 
    B --> C[List&lt;TextNode&gt;]
    C --> D[Embedded Nodes]
    D --> E[Vector Store]
    E --> F[RAG Agents]
    
    style A fill:#2196f3
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#9c27b0
    style F fill:#4caf50
```

::: info Data Transformation Stages
1. **`DataLakeFile`** → **`RefDocDocument`**: Parse document content and extract metadata
2. **`RefDocDocument`** → **`List<TextNode>`**: Intelligent chunking for optimal retrieval
3. **`List<TextNode>`** → **`Embedded Nodes`**: Generate vector embeddings
4. **`Embedded Nodes`** → **`Vector Store`**: Index for fast similarity search
5. **`Vector Store`** → **`RAG Agents`**: Enable knowledge retrieval and question answering
:::

Each stage adds value and maintains traceability back to the original source, ensuring RAG agents can provide accurate, source-attributed responses.

## Partitioning for scalability {#partitioning}

### Dynamic partitions {#dynamic-partitions}

> [!TIP]
> Use **Dynamic Partitions** to handle datasets where individual items (documents, files) need separate processing.

::: code-group

```python [Partition Definition]
document_partitions = DynamicPartitionsDefinition(name="document_partitions")
```

```python [Partition Benefits]
# This allows the pipeline to:
# - Process each document independently
# - Add new partitions as documents arrive  
# - Reprocess only changed documents
# - Scale processing across multiple workers
```

:::

### Partition benefits {#partition-benefits}

::: info Scalability Advantages
- **Parallelization**: Process multiple documents simultaneously
- **Incremental updates**: Only reprocess changed content
- **Failure isolation**: One document failure doesn't break the entire pipeline
- **Resource efficiency**: Allocate compute resources based on actual workload
:::

## Asset automation and dependencies {#automation}

### Automation conditions {#automation-conditions}

Control when assets materialize using automation conditions:

::: code-group

```python [Eager Automation]
@graph_asset(
    automation_condition=AutomationCondition.eager(),  # Run immediately
)
def immediate_processing(...):
    """Runs immediately when dependencies change."""
    pass
```

```python [Scheduled Automation]
@graph_asset(
    automation_condition=AutomationCondition.cron_tick_passed("0 9 * * *"),
)
def daily_processing(...):
    """Runs daily at 9 AM."""
    pass
```

```python [Combined Conditions]
business_hours_condition = (
    AutomationCondition.eager() &  # Eager when dependencies change
    AutomationCondition.cron_tick_passed("0 9-17 * * MON-FRI")  # Business hours only
)
```

:::

### Dependency management {#dependencies}

Assets automatically track dependencies through their `ins` parameter:

```python
@graph_asset(
    ins={"document": AssetIn(key=document_key)},  # Depends on document asset
    partitions_def=partitions,
)
def nodes(document: RefDocDocument) -> List[TextNode]:
    """Automatically runs when document asset materializes."""
    return chunk_document_into_nodes(document)
```

## Configuration patterns {#configuration}

### Environment-specific resources {#env-resources}

Create different resource configurations for different environments:

::: code-group

```python [Development Resources]
def development_resources():
    """Local development setup."""
    return {
        **local_mongo_milvus_storage_context_resource(
            vector_store_uri="http://localhost:19530",
        ),
        "document_parser": DocumentParserResource(
            loader_type=LoaderType.DOCLING
        ),
    }
```

```python [Production Resources]
def production_resources():
    """Production environment setup.""" 
    return {
        **mongo_aisearch_storage_context_resources(
            store_name="prod_store"
        ),
        "document_parser": DocumentParserResource(
            loader_type=LoaderType.BOTH,
            timeout=300,
        ),
    }
```

:::

### Asset composition {#asset-composition}

Combine multiple asset factories to create complete processing pipelines:

::: details Complete Pipeline Example
```python
# Create all pipeline assets
assets = [
    observable_data_lake_factory(DATA_LAKE_KEY, document_partitions),
    documents_factory(DOCUMENT_KEY, DATA_LAKE_KEY, document_partitions),
    nodes_factory(NODES_KEY, DOCUMENT_KEY, document_partitions),
    summary_nodes_factory(SUMMARY_KEY, DOCUMENT_KEY, NODES_KEY, document_partitions),
]

# Define complete pipeline
defs = Definitions(
    assets=assets,
    resources=development_resources(),
    schedules=[daily_schedule_at(observe_job, hour=2, minute=0)],
    sensors=[default_automation_sensor(assets)],
)
```
:::

## Getting started {#getting-started}

### Examine the playground {#playground}

> [!IMPORTANT]
> The best way to understand pipeline fundamentals is to examine the working example in the playground.

::: code-group

```bash [Start Development Server]
cd aihub_pipeline
poetry shell
# Start the Dagster development server
make playground
```

```bash [Alternative Command]
poetry run dagster dev -m playground
```

:::

Navigate to `http://localhost:3000` to explore the pipeline visually in the Dagster web interface.

### Key files to examine {#key-files}

::: info Important Files
- [`playground/__init__.py`](../../aihub_pipeline/playground/__init__.py) - Complete pipeline definition
- [`assets/factories/`](../../aihub_pipeline/aihub_pipeline/assets/factories/) - Asset factory patterns  
- [`ops/`](../../aihub_pipeline/aihub_pipeline/ops/) - Individual operation implementations
- [`resources/`](../../aihub_pipeline/aihub_pipeline/resources/) - Resource configurations
:::

### Development workflow {#workflow}

::: tip Development Steps
1. **Start with the playground** - Understand existing patterns
2. **Create your asset factories** - Build reusable components
3. **Define operations** - Implement processing logic
4. **Configure resources** - Set up external dependencies
5. **Test locally** - Use the Dagster web interface
6. **Deploy to production** - Follow production deployment patterns
:::

## Next steps {#next-steps}

Once you understand these fundamentals, you're ready to explore:

::: info Next Topics
- [Data ingestion patterns](../2_data_ingestion_patterns/) for common document processing scenarios
- [Observable assets](../3_observable_assets/) for building reactive pipelines
- [Testing pipelines](../4_testing_pipelines/) for ensuring reliability
:::