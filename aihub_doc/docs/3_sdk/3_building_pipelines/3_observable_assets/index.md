---
title: Observable Assets
index: 3
---

# Observable Assets

Observable assets are special assets that monitor external data sources for changes and automatically trigger downstream processing when new data is detected.

## What you'll learn

This guide covers observable assets:
- **Monitoring**: How to watch external data sources for changes
- **Partitions**: Creating dynamic partitions for new data
- **Data Versions**: Tracking changes with content-based versioning
- **Automation**: Triggering downstream assets automatically

## How observable assets work

Observable assets solve a key problem in data pipelines: **knowing when external data has changed**. Observable assets:

- **Monitor external sources** like file systems i.e. Data Lake, SharePoint, etc.  
- **Detect new or changed data** by comparing content hashes or timestamps  
- **Create dynamic partitions** for each piece of data (e.g., one partition per file)
- **Trigger downstream processing** automatically when changes are detected

## Understanding the AI-Hub observable data lake asset

Let's look at how AI-Hub uses observable assets to monitor data lakes for document processing.

### 1. The observable data lake factory:

```python
# Simplified version of aihub_pipeline/assets/factories/data_lake_to_vector_store/observable_data_lake_factory.py
from dagster import (
    AssetKey,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
    ResourceParam,
    observable_source_asset,
)

from aihub_pipeline.types.DataLakeFile import DataLakeFile

def observable_data_lake_factory(
    key: AssetKey, 
    partitions: DynamicPartitionsDefinition
) -> observable_source_asset:
    """Creates an observable source asset that monitors a data lake for file changes."""
    
    @observable_source_asset(
        key=key,
        partitions_def=partitions,
        io_manager_key="data_lake_io_manager",
        description="Observes the data lake for any changes with respect to the Document Store",
    )
    def observable_data_lake(
        context: OpExecutionContext,
        data_lake_client: ResourceParam[FileSystemClient],
        data_lake_resource: DataLakeResource,
    ) -> DataVersionsByPartition:
        """Monitor data lake for new or changed files."""
        
        # Fetch all files from the data lake using AI-Hub operations
        data_lake_files: list[DataLakeFile] = fetch_all_files_in_data_lake_no_op(
            data_lake_client=data_lake_client,
            data_lake_container_name=data_lake_resource.container_name,
            data_lake_directory_name=data_lake_resource.directory_name,
        )
        
        # Generate data versions and partitions
        return data_version_by_partition_for_data_lake_files_no_op(
            context=context,
            asset_key=key,
            partition=partitions,
            data_lake_files=data_lake_files,
        )
    
    return observable_data_lake
```

### 2. Data versioning logic:

```python
# From aihub_pipeline/ops/data_lake/data_version_by_partition_for_data_lake_files.py
def data_version_by_partition_for_data_lake_files_no_op(
    context: OpExecutionContext,
    asset_key: AssetKey,
    partition: DynamicPartitionsDefinition,
    data_lake_files: list[DataLakeFile],
) -> DataVersionsByPartition:
    """Generates dynamic partitions and data versions for data lake files."""
    
    # Replace partition keys with current file URIs
    replace_partition_keys(
        context,
        partition.name,
        [data_lake_file.uri for data_lake_file in data_lake_files],
    )
    
    context.log.info(f"Found {len(data_lake_files)} files in the data lake")
    
    # Report asset materialization with metadata
    if len(data_lake_files) > 0:
        context.instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=asset_key,
                partition=data_lake_files[-1].uri,
                metadata={
                    "Number of Files": len(data_lake_files),
                    "Total File Size (MB)": sum([f.size for f in data_lake_files]) / 1e6,
                    "Table": data_lake_metadata_table(data_lake_files),
                },
            )
        )
    
    # Create data versions: timestamp + hash ensures deleted/re-added files are reprocessed
    return DataVersionsByPartition({
        data_lake_file.uri: f"{data_lake_file.updated}-{data_lake_file.hash}" 
        for data_lake_file in data_lake_files
    })
```

### 3. Downstream processing assets:

Create assets that process the observed data lake files:

```python
# From aihub_pipeline/assets/factories/data_lake_to_vector_store/documents_factory.py
from dagster import AssetIn, AssetKey, AutomationCondition, DynamicPartitionsDefinition, Output, graph_asset

def documents_factory(
    key: AssetKey, data_lake_key: str | AssetKey, partitions: DynamicPartitionsDefinition
) -> graph_asset:
    """Creates a document asset that processes data lake files into RefDocs."""
    
    @graph_asset(
        key=key,
        ins={"data_lake_file": AssetIn(key=data_lake_key)},
        partitions_def=partitions,
        automation_condition=AutomationCondition.eager(),
        description="Create RefDocs from data lake files and insert them into the docstore",
    )
    def document(data_lake_file: DataLakeFile) -> Output[RefDocDocument]:
        return insert_ref_doc_into_docstore(
            ensure_refdoc_default_metadata(
                generate_figure_descriptions(
                    parse_document_from_data_lake(data_lake_file)
                )
            )
        )
    
    return document

# From aihub_pipeline/assets/factories/data_lake_to_vector_store/nodes_factory.py  
def nodes_factory(
    key: AssetKey, document_key: str | AssetKey, partitions: DynamicPartitionsDefinition
) -> graph_asset:
    """Creates nodes from processed documents for vector storage."""
    
    @graph_asset(
        key=key,
        ins={"document": AssetIn(key=document_key)},
        partitions_def=partitions,
        automation_condition=AutomationCondition.eager(),
        description="Chunks a RefDoc into Nodes and inserts them into the Vector Store",
    )
    def nodes(document: RefDocDocument) -> Output[list[TextNode]]:
        return insert_nodes_into_vector_store(
            embed_nodes(
                ensure_node_default_metadata(
                    chunk_ref_doc_into_nodes_using_md_structural_node_parser(
                        delete_nodes_for_ref_doc(document)
                    )
                )
            ),
            document,
        )
    
    return nodes
```

### 4. How it all works together 

```python
# From aihub_pipeline/playground/__init__.py (simplified)
from dagster import AssetKey, Definitions, DynamicPartitionsDefinition

# Asset configuration
DATA_LAKE_KEY = AssetKey(["playground", "data_lake"])
DOCUMENT_KEY = AssetKey(["playground", "documents"])
NODES_KEY = AssetKey(["playground", "nodes"])

document_partitions = DynamicPartitionsDefinition(name="document_partitions")

# Create assets using factories
observable_asset = observable_data_lake_factory(DATA_LAKE_KEY, document_partitions)
documents = documents_factory(DOCUMENT_KEY, data_lake_key=DATA_LAKE_KEY, partitions=document_partitions)
nodes = nodes_factory(NODES_KEY, document_key=DOCUMENT_KEY, partitions=document_partitions)

# Pipeline definition
defs = Definitions(
    assets=[observable_asset, documents, nodes],
    resources={
        **s3_data_lake_resources(
            container_name="playground",
            directory_name="test",
            figures_directory_name="__figures__",
        ),
        "document_parser": DocumentParserResource(loader_type=LoaderType.DOCLING),
        "node_parser": MarkdownStructuralNodeParserResource(),
        **local_mongo_milvus_storage_context_resource(
            vector_store_uri="http://localhost:19530",
            store_name="playground",
            namespace_name="test",
        ),
        "embedding_model": EmbeddingModelResource(
            embedding_config=EmbeddingModelConfig(model_name="azure/text-embedding-3-large"),
        ),
    },
    sensors=[default_automation_sensor([observable_asset, documents, nodes])],
)
```

## Understanding the patterns

### Data Versions with AI-Hub
```python
# AI-Hub combines timestamp and hash to ensure reprocessing of deleted/re-added files
return DataVersionsByPartition({
    data_lake_file.uri: f"{data_lake_file.updated}-{data_lake_file.hash}" 
    for data_lake_file in data_lake_files
})
```

### Dynamic Partitions
```python
# Each data lake file URI becomes its own partition
replace_partition_keys(
    context,
    partition.name,
    [data_lake_file.uri for data_lake_file in data_lake_files],
)
```

### Factory Pattern for Reusability
```python
# Create reusable asset factories for different environments
observable_asset = observable_data_lake_factory(DATA_LAKE_KEY, document_partitions)
documents = documents_factory(DOCUMENT_KEY, data_lake_key=DATA_LAKE_KEY, partitions=document_partitions)
```

## Real-world use cases

Observable assets are used for:

- **Document processing**: Monitor SharePoint, data lakes, or file systems for new documents
- **RAG pipeline updates**: Automatically reprocess documents when content changes
- **Scalable ingestion**: Each document is processed independently as its own partition
- **Compliance and audit**: Full traceability of which data version was used for each processing run

## What you learned

- **Observable assets**: Monitor data lakes for document changes using AI-Hub patterns
- **Dynamic partitions**: Process each document as an independent partition
- **Data versioning**: Combine timestamps and hashes for reliable change detection
- **Asset factories**: Create reusable, configurable pipeline components
- **Production-ready patterns**: Use the same observable assets running in AI-Hub production

## Next steps

- [Testing Pipelines](/3_sdk/3_building_pipelines/4_testing_pipelines/) - Test observable assets and pipeline components
- [Resources](/3_sdk/3_building_pipelines/5_production_scheduling/) - Configure external services and scheduling
- Explore `aihub_pipeline/playground/__init__.py` for the complete observable pipeline example