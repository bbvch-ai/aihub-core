---
title: Pipeline Patterns
index: 1
---

# Pipeline Patterns

The specific Dagster patterns that power the `aihub_pipeline` SDK. Understanding these patterns enables developers to
build robust, scalable pipelines using the same architectural foundations.

## 1. Observable Assets - Change Detection Based on Hashes

Observable assets monitor external data sources and detect changes using content hashes and/or timestamps. They create
dynamic partitions when new data is discovered.

```python
@observable_source_asset(
    key=AssetKey(["data_lake"]),
    group_name=group_name_from_asset_key(AssetKey(["data_lake"])),
    partitions_def=DynamicPartitionsDefinition(name="my_documents"),
    io_manager_key="data_lake_io_manager",
    description="Observes the data lake for any changes with respect to the Document Store",
)
def observable_data_lake(
    context: OpExecutionContext,
    data_lake_client: ResourceParam[FileSystemClient],
    data_lake_resource: DataLakeResource,
) -> DataVersionsByPartition:
    """Monitor data lake for changed files using hash-based detection."""
    
    # Fetch all files from the data lake
    data_lake_files: list[DataLakeFile] = fetch_all_files_in_data_lake_no_op(
        data_lake_client=data_lake_client,
        data_lake_container_name=data_lake_resource.container_name,
        data_lake_directory_name=data_lake_resource.directory_name,
        data_lake_figures_directory_name=data_lake_resource.figures_directory_name,
    )
    
    # Generate data versions and update partitions
    return data_version_by_partition_for_data_lake_files_no_op(
        context=context,
        asset_key=AssetKey(["data_lake"]),
        partition=DynamicPartitionsDefinition(name="my_documents"),
        data_lake_files=data_lake_files,
    )
```

### The Core Data Versioning Logic

The `data_version_by_partition_for_data_lake_files_no_op` function is the heart of change detection:

```python
from dagster import (
    AssetKey,
    AssetMaterialization,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
)

from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.util.meta_utils import data_lake_metadata_table
from aihub_pipeline.util.partition_utils import replace_partition_keys

def data_version_by_partition_for_data_lake_files_no_op(
    context: OpExecutionContext,
    asset_key: AssetKey,
    partition: DynamicPartitionsDefinition,
    data_lake_files: list[DataLakeFile],
) -> DataVersionsByPartition:
    """Generates dynamic partitions and data versions for data lake files."""
    
    # Create/update partition keys with current file URIs
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
    
    # Critical: timestamp + hash ensures deleted/re-added files are reprocessed
    # If we only used hash, Dagster would think a deleted+re-added file was already processed
    return DataVersionsByPartition({
        data_lake_file.uri: f"{data_lake_file.updated}-{data_lake_file.hash}" 
        for data_lake_file in data_lake_files
    })
```

**Why timestamp + hash is critical:**

- **File deletion handling**: If a file is deleted and re-added with identical content, the hash alone would be the same
- **Dagster optimization**: Dagster assumes files with identical data versions were already processed
- **Reprocessing guarantee**: The timestamp component ensures deleted/re-added files trigger reprocessing
- **Future improvement**: When Dagster resolves issue [#14749](https://github.com/dagster-io/dagster/issues/14749),
  `wipe_asset_partitions` will enable using hash-only versioning

**Key aspects of observable assets:**

- **Hash-based change detection**: Combines file timestamps and content hashes
- **Dynamic partition creation**: Each file URI becomes a partition key
- **Asset materialization reporting**: Provides rich metadata about discovered files
- **Efficient processing**: Only changed files trigger downstream processing
- **Deletion handling**: Timestamp+hash versioning handles file deletion scenarios

## 2. Dynamic Partitions - Per-Document Processing

Each document gets its own partition, enabling independent, parallel processing with fault isolation.

```python
# Define dynamic partitions that grow as documents are discovered
document_partitions = DynamicPartitionsDefinition(name="my_documents")

@graph_asset(
    key=AssetKey(["documents"]),
    ins={"data_lake_file": AssetIn(key=AssetKey(["data_lake"]))},
    partitions_def=document_partitions,
    automation_condition=AutomationCondition.eager(),
)
def documents(data_lake_file: DataLakeFile) -> RefDocDocument:
    """Each document is processed in its own partition."""
    return process_single_document(data_lake_file)
```

**Benefits of dynamic partitions:**

- **Fault isolation**: Failure processing one document doesn't affect others
- **Parallel processing**: Multiple documents can be processed simultaneously
- **Selective reprocessing**: Only changed documents are reprocessed
- **Scalability**: Add more workers to increase throughput

## 3. I/O Managers - Data Flow Between Operations

I/O managers handle loading inputs and storing outputs for assets. They sit between operations and manage data
persistence.

::: code-group
```python [I/O Manager]
class DocStoreIOManager(IOManager):
    """I/O manager for RefDocDocument objects in MongoDB."""
    
    def handle_output(self, context: OutputContext, obj: RefDocDocument) -> None:
        """Store RefDocDocument in MongoDB after operation completes."""
        doc_store = context.resources.doc_store
        
        # Store document with partition-based ID
        document_data = {
            "doc_id": context.partition_key,
            "content": obj.text,
            "metadata": obj.metadata,
            "created_at": datetime.utcnow(),
        }
        
        doc_store.insert_document(document_data)
        context.log.info(f"Stored RefDocDocument {context.partition_key} in document store")
    
    def load_input(self, context: InputContext) -> RefDocDocument:
        """Load RefDocDocument from MongoDB before operation starts."""
        doc_store = context.resources.doc_store
        
        # Retrieve document by partition key
        document_data = doc_store.get_document(context.partition_key)
        if not document_data:
            raise ValueError(f"Document {context.partition_key} not found in doc store")
        
        return RefDocDocument(
            doc_id=document_data["doc_id"],
            text=document_data["content"],
            metadata=document_data["metadata"],
        )
```

```python [Usage]
@op(code_version="v1", out=Out(io_manager_key="doc_store_io_manager"))
def insert_ref_doc_into_docstore(ref_doc: RefDocDocument) -> Output[RefDocDocument]:
    """Inserts a RefDocDocument into the Document Store by having the appropriate
    IO manager set as the output IO Manager.
    """
    return Output(
        ref_doc,
        metadata=ref_doc_metadata(ref_doc),
        data_version=DataVersion(f"{ref_doc.updated}-{ref_doc.hash}"),
    )



# ...

defs = Definitions(
    # ...
    
    resources={
        "doc_store_io_manager": DocStoreIOManager(
            doc_store=MongoDocumentStoreResource(document_store_name="my_docs")
        ), 
    }
)
```
:::

**I/O manager responsibilities:**

- **Input loading**: Automatically fetch data from storage systems before operations run
- **Output storing**: Automatically persist operation results to appropriate storage
- **Type safety**: Handle specific data types with optimized serialization
- **Storage abstraction**: Operations don't need to know about storage implementation details
- **Partition awareness**: Use partition keys to organize data storage and retrieval

## 4. Resources - External System Management

Resources provide configuration, authentication, connections and operations to external systems.

```python
from aihub_lib.persistence.rag.documents.stores.docstore import create_mongo_document_store
from dagster import ConfigurableResource, InitResourceContext
from llama_index.storage.docstore.mongodb import MongoDocumentStore


class MongoDocumentStoreResource(ConfigurableResource[MongoDocumentStore]):
    """
    This resource represents a MongoDocumentStore with an active connection.

    Use this resource either stand-alone whenever you want to directly interact with the document store,
    or use it in conjunction with the ``"doc_store_io_manager"`` resource for a more integrated experience.
    """

    document_store_name: str

    def create_resource(self, context: InitResourceContext) -> MongoDocumentStore:
        return create_mongo_document_store(self.document_store_name)
```

**Resource responsibilities:**

- **Authentication**: Handle API keys, connection strings, and credentials
- **Configuration**: Provide settings like timeouts, retries, and endpoints
- **Connection management**: Maintain database connections and client instances
- **Error handling**: Implement retry logic and failure recovery

## 5. Graph Assets - Composing Complex Operations

Graph assets are assets composed of multiple operations (ops) that work together to produce a final output.

```python
@op
def parse_document_from_data_lake(data_lake_file: DataLakeFile) -> RefDocDocument:
    """Parse document content from data lake file."""
    return parse_document(data_lake_file)

@op  
def ensure_refdoc_default_metadata(document: RefDocDocument) -> RefDocDocument:
    """Add default metadata to document."""
    document.metadata.update({
        "processed_at": datetime.utcnow().isoformat(),
        "version": "1.0"
    })
    return document

@op
def insert_ref_doc_into_docstore(document: RefDocDocument) -> RefDocDocument:
    """Store document in document store."""
    doc_store = get_current_context().resources.doc_store
    doc_store.insert_document(document)
    return document

@graph_asset(
    key=AssetKey(["documents"]),
    ins={"data_lake_file": AssetIn(key=AssetKey(["data_lake"]))},
    partitions_def=document_partitions,
    automation_condition=AutomationCondition.eager(),
)
def documents(data_lake_file: DataLakeFile) -> RefDocDocument:
    """Process documents through multiple operations."""
    return insert_ref_doc_into_docstore(
        ensure_refdoc_default_metadata(
            parse_document_from_data_lake(data_lake_file)
        )
    )
```

**Graph asset characteristics:**

- **Operation composition**: Chain multiple ops to create complex processing
- **Reusable ops**: Individual ops can be reused across different graph assets
- **Clear data flow**: Each op receives typed inputs and produces typed outputs
- **Intermediate materialization**: Ops can store intermediate results for debugging

## 6. Asset Factories - Reusable Pipeline Components

Asset factories are functions that create configured assets, enabling reusable pipeline components.

```python
def documents_factory(
    key: AssetKey,
    data_lake_key: AssetKey,
    partitions: DynamicPartitionsDefinition,
) -> graph_asset:
    """Factory that creates a document processing asset."""
    
    @graph_asset(
        key=key,
        ins={"data_lake_file": AssetIn(key=data_lake_key)},
        partitions_def=partitions,
        automation_condition=AutomationCondition.eager(),
        description="Process data lake files into RefDoc documents",
    )
    def documents(data_lake_file: DataLakeFile) -> RefDocDocument:
        return insert_ref_doc_into_docstore(
            ensure_refdoc_default_metadata(
                generate_figure_descriptions(
                    parse_document_from_data_lake(data_lake_file)
                )
            )
        )
    
    return documents


# Using factories to create a pipeline
partitions = DynamicPartitionsDefinition(name="company_documents")

assets = [
    documents_factory(
        key=AssetKey(["company", "documents"]),
        data_lake_key=AssetKey(["company", "data_lake"]),
        partitions=partitions,
    ),
]
```

**Asset factory benefits:**

- **Reusability**: Same factory can create assets for different environments
- **Parameterization**: Customize asset behavior through factory parameters
- **Consistency**: Ensures assets are created with proper configuration
- **Maintainability**: Changes to asset logic only need to be made in one place

## 7. Resource Factory Pattern

Resource factory functions create complete sets of resources for different environments, ensuring consistent
configuration.

```python
def local_mongo_milvus_storage_context_resource(
    vector_store_uri: str,
    store_name: str,
    namespace_name: str,
) -> dict[str, ConfigurableResource]:
    """Complete resource set for local development with MongoDB + Milvus."""
    return {
        "doc_store": MongoDocumentStoreResource(
            connection_string="mongodb://localhost:27017",
            store_name=store_name,
        ),
        "vector_store": MilvusVectorStoreResource(
            vector_store_uri=vector_store_uri,
            namespace_name=namespace_name,
        ),
        "doc_store_io_manager": DocStoreIOManager(),
        "vector_store_io_manager": VectorStoreIOManager(),
    }

# Usage
defs = Definitions(
    assets=assets,
    resources=local_mongo_milvus_storage_context_resource(
        vector_store_uri="http://localhost:19530",
        store_name="development_kb",
        namespace_name="dev"
    ),
)
```

**Resource factory benefits:**

- **Environment consistency**: Same pipeline code works across dev/test/prod
- **Complete configuration**: All related resources configured together
- **Easy switching**: Change environments by swapping factory functions
- **No configuration drift**: Resources always configured consistently

## Pattern Summary

These Dagster patterns work together to create efficient, maintainable pipelines:

- **Observable Assets**: Monitor external data sources using content hashes and timestamps
- **Dynamic Partitions**: Process each document independently for fault isolation and parallelism
- **I/O Managers**: Handle data persistence between operations and storage systems
- **Resources**: Manage external system connections, authentication, and configuration
- **Graph Assets**: Compose complex processing from reusable operations
- **Asset Factories**: Create configurable, reusable pipeline components


## Next steps

- [Data Ingestion Pipeline](../2_data_ingestion_pipeline/) - Apply these patterns to a working pipeline
