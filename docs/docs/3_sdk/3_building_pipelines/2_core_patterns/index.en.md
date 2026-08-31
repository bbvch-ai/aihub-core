---
title: Core Patterns
---

# Core Pipeline Patterns

This page provides practical code examples for the concepts introduced in
[Pipeline Fundamentals](../1_pipeline_fundamentals/). These are the patterns you will use to build, customize, and
extend document processing pipelines with the `swiss_ai_hub.pipeline` SDK.

## Change Detection with Observable Assets

This pattern is the trigger for our automated pipelines. An `observable_source_asset` monitors an external data source
and yields a new data version for each file, typically by combining its timestamp and content hash. Dagster only
materializes downstream assets if this version has changed.

```python
# From observable_data_lake_factory.py
@observable_source_asset(
    key=AssetKey(["data_lake"]),
    partitions_def=document_partitions,
    description="Observes the data lake for new or changed files",
)
def observable_data_lake(context: OpExecutionContext) -> DataVersionsByPartition:
    # 1. Fetch all files from the data lake source
    data_lake_files: list[DataLakeFile] = fetch_all_files_in_data_lake_no_op(...)
    
    # 2. For each file's partition, create a unique version key
    # This tells Dagster whether the file is new or has been modified.
    return DataVersionsByPartition({
        file.uri: f"{file.updated}-{file.hash}" for file in data_lake_files
    })
```

## Per-Document Processing with Dynamic Partitions

Each document discovered by the observable asset is assigned its own partition, allowing for isolated and parallel
processing.

- **`DynamicPartitionsDefinition`**: Defines a set of partitions that can grow over time.
- **`automation_condition=AutomationCondition.eager()`**: This tells Dagster to automatically run this asset for a
  partition as soon as its upstream dependency (the observable asset) has a new version for that partition.

```python
# Define a set of partitions that will be populated with document URIs
document_partitions = DynamicPartitionsDefinition(name="my_documents")

@graph_asset(
    key=AssetKey(["documents"]),
    ins={"data_lake_file": AssetIn(key=AssetKey(["data_lake"]))},
    partitions_def=document_partitions,
    automation_condition=AutomationCondition.eager(),
)
def documents(data_lake_file: DataLakeFile) -> RefDocDocument:
    """This asset will execute once for each new or changed document."""
    return process_single_document(data_lake_file)
```

## Abstracting Storage with I/O Managers

I/O Managers connect assets by handling data persistence. They are configured as resources and assigned to assets.

```python
# From DocStoreIOManager.py
class DocStoreIOManager(ConfigurableIOManager):
    doc_store: ResourceDependency[KVDocumentStore]

    def handle_output(self, context: OutputContext, obj: RefDocDocument) -> None:
        """Saves the RefDocDocument produced by an asset to MongoDB."""
        context.log.info(f"Adding document to docstore: {obj.id_}")
        self.doc_store.add_documents([obj])

    def load_input(self, context: InputContext) -> RefDocDocument:
        """Loads a RefDocDocument from MongoDB for a downstream asset."""
        doc_id = self._convert_partition_key_to_doc_id(context.partition_key, context)
        document = self.doc_store.get_document(doc_id)
        return RefDocDocument(**document.to_dict())

# In your definitions, you provide the I/O Manager as a resource
defs = Definitions(
    assets=[...],
    resources={
        "doc_store": MongoDocumentStoreResource(...),
        "doc_store_io_manager": DocStoreIOManager(),
    }
)
```

## Composing Logic with Graph Assets

A `graph_asset` is an asset composed of multiple smaller functions called **ops** (`@op`). This allows you to build
complex transformations while keeping each piece of logic simple and reusable.

```python
# From documents_factory.py
@graph_asset(key=key, ...)
def document(data_lake_file: DataLakeFile) -> Output[RefDocDocument]:
    """
    This graph asset defines a multi-step process for a single document.
    The output of one op flows directly into the next.
    """
    # Op 1: Parse the raw file
    parsed_doc = parse_document_from_data_lake(data_lake_file)
    # Op 2: Add default metadata
    doc_with_metadata = ensure_refdoc_default_metadata(parsed_doc)
    # Op 3: Save to the document store (via I/O Manager)
    return insert_ref_doc_into_docstore(doc_with_metadata)
```

## Building Reusable Pipelines with Factories

Factories are the highest level of abstraction in the SDK. They are functions that generate fully configured assets and
resources, allowing you to define an entire pipeline in just a few lines of code.

- **Asset Factories (`*_factory.py`)**: Functions that create individual, configured assets (like `documents_factory`).
- **Resource Factories (`resources/factory.py`)**: Functions that assemble a complete set of resources needed for a
  pipeline (like `s3_data_lake_resources`).
- **Definitions Factories (`rag_definitions_util.py`)**: The top-level factory (`rag_pipeline_definitions`) that uses
  all other factories to create a complete, runnable `Definitions` object.

```python
# From rag_definitions_util.py
def rag_pipeline_definitions(ingestor: str = "rag", ...) -> Definitions:
    """
    A factory that assembles an entire pipeline from other factories.
    """
    # Use asset factories to create the assets
    observable_asset = observable_data_lake_factory(...)
    documents_asset = documents_factory(...)
    nodes_asset = nodes_factory(...)

    assets = [observable_asset, documents_asset, nodes_asset]

    # Use resource factories to create the resources
    resources = {
        **default_io_manager_s3_datalake_resources(container_name=datalake_container_name),
        **local_mongo_milvus_storage_context_resource(...),
        # ... other resources
    }
    
    return Definitions(assets=assets, resources=resources, ...)
```
