---
title: Kernmuster
source_sha: ac28b8232bb5926aed13b2258a0065ead68f0a42eab2f8aeef82027f77221dfe
---

# Kern-Pipeline-Muster

Diese Seite bietet praktische Codebeispiele für die Konzepte, die in [Pipeline-Grundlagen](../1_pipeline_fundamentals/)
vorgestellt wurden. Dies sind die Muster, die Sie verwenden werden, um Dokumentverarbeitungs-Pipelines mit dem
`swiss_ai_hub.pipeline` SDK zu erstellen, anzupassen und zu erweitern.

## Änderungserkennung mit beobachtbaren Assets

Dieses Muster ist der Auslöser für unsere automatisierten Pipelines. Ein `observable_source_asset` überwacht eine
externe Datenquelle und erzeugt für jede Datei eine neue Datenversion, typischerweise durch Kombination ihres
Zeitstempels und ihres Inhaltshashs. Dagster materialisiert nachgelagerte Assets nur, wenn sich diese Version geändert
hat.

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

## Dokumentweise Verarbeitung mit dynamischen Partitionen

Jedes von einem beobachtbaren Asset entdeckte Dokument erhält seine eigene Partition, was eine isolierte und parallele
Verarbeitung ermöglicht.

- **`DynamicPartitionsDefinition`**: Definiert einen Satz von Partitionen, die im Laufe der Zeit wachsen können.
- **`automation_condition=AutomationCondition.eager()`**: Dies weist Dagster an, dieses Asset für eine Partition
  automatisch auszuführen, sobald dessen Upstream-Abhängigkeit (das beobachtbare Asset) eine neue Version für diese
  Partition hat.

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

## Abstraktion der Speicherung mit I/O-Managern

I/O-Manager verbinden Assets, indem sie die Datenpersistenz handhaben. Sie werden als Ressourcen konfiguriert und Assets
zugewiesen.

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

## Logikkomposition mit Graph-Assets

Ein `graph_asset` ist ein Asset, das aus mehreren kleineren Funktionen, sogenannten **Ops** (`@op`), besteht. Dies
ermöglicht es Ihnen, komplexe Transformationen zu erstellen, während jeder Logikbaustein einfach und wiederverwendbar
bleibt.

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

## Wiederverwendbare Pipelines mit Factories erstellen

Factories sind die höchste Abstraktionsebene im SDK. Es sind Funktionen, die vollständig konfigurierte Assets und
Ressourcen generieren, sodass Sie eine gesamte Pipeline mit nur wenigen Codezeilen definieren können.

- **Asset Factories (`*_factory.py`)**: Funktionen, die individuelle, konfigurierte Assets erstellen (wie
  `documents_factory`).
- **Resource Factories (`definitions_util.py`)**: Funktionen, die einen vollständigen Satz von Ressourcen für eine
  Pipeline zusammenstellen (wie `local_mongo_milvus_storage_context_resource`).
- **Definitions Factories (`definitions_util.py`)**: Die Top-Level-Factory (`default_definitions`), die alle anderen
  Factories verwendet, um ein vollständiges, ausführbares `Definitions`-Objekt zu erstellen.

```python
# From definitions_util.py
def default_definitions(datalake_container_name: str, ...) -> Definitions:
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
