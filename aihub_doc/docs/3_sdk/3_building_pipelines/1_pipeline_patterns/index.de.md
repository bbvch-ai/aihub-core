---
title: Pipeline-Muster
index: 1
source_sha: "c1d08aa48b39a4ef432f4ef5304c078e7945565db50b9f0967b1e0586d9289b0"
---

# Pipeline-Muster

Die spezifischen Dagster-Muster, die das `aihub_pipeline` SDK antreiben. Das Verständnis dieser Muster ermöglicht es Entwicklern,
robuste, skalierbare Pipelines unter Verwendung derselben architektonischen Grundlagen zu erstellen.

## Was Sie lernen werden

-   **Observable Assets**: Wie Änderungen in externen Datenquellen basierend auf Inhaltshashes erkannt werden
-   **Dynamic Partitions**: Dynamisches Erstellen von Partitionen, sobald neue Daten entdeckt werden
-   **I/O Managers**: Wie Daten zwischen Operationen und Speichersystemen fließen
-   **Resources**: Verwaltung externer Systemverbindungen und Konfigurationen
-   **Graph Assets**: Zusammensetzen komplexer Operationen aus einfachen Bausteinen
-   **Asset Factories**: Erstellen wiederverwendbarer Pipeline-Komponenten

## 1. Observable Assets – Änderungserkennung basierend auf Hashes

Observable Assets überwachen externe Datenquellen und erkennen Änderungen mithilfe von Inhaltshashes und/oder Zeitstempeln. Sie erstellen
dynamische Partitionen, wenn neue Daten entdeckt werden.

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

### Die Kernlogik der Datenversionierung

Die Funktion `data_version_by_partition_for_data_lake_files_no_op` ist das Herzstück der Änderungserkennung:

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

**Warum Zeitstempel + Hash entscheidend ist:**

-   **Handhabung von Dateilöschungen**: Wenn eine Datei gelöscht und mit identischem Inhalt erneut hinzugefügt wird, wäre der Hash allein derselbe
-   **Dagster-Optimierung**: Dagster nimmt an, dass Dateien mit identischen Datenversionen bereits verarbeitet wurden
-   **Garantie der Neuverarbeitung**: Die Zeitstempelkomponente sorgt dafür, dass gelöschte/erneut hinzugefügte Dateien eine Neuverarbeitung auslösen
-   **Zukünftige Verbesserung**: Wenn Dagster das Problem [#14749](https://github.com/dagster-io/dagster/issues/14749) löst,
    wird `wipe_asset_partitions` die Verwendung einer reinen Hash-Versionierung ermöglichen

**Wichtige Aspekte von Observable Assets:**

-   **Hash-basierte Änderungserkennung**: Kombiniert Dateizeitstempel und Inhaltshashes
-   **Dynamische Partitionsbildung**: Jeder Datei-URI wird zu einem Partitionsschlüssel
-   **Meldung der Asset-Materialisierung**: Bietet umfangreiche Metadaten zu entdeckten Dateien
-   **Effiziente Verarbeitung**: Nur geänderte Dateien lösen die nachgelagerte Verarbeitung aus
-   **Handhabung von Löschungen**: Zeitstempel+Hash-Versionierung handhabt Dateilöschszenarien

## 2. Dynamic Partitions – Verarbeitung pro Dokument

Jedes Dokument erhält eine eigene Partition, was eine unabhängige, parallele Verarbeitung mit Fehlerisolation ermöglicht.

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

**Vorteile dynamischer Partitionen:**

-   **Fehlerisolation**: Ein Fehler bei der Verarbeitung eines Dokuments beeinträchtigt keine anderen
-   **Parallele Verarbeitung**: Mehrere Dokumente können gleichzeitig verarbeitet werden
-   **Selektive Neuverarbeitung**: Nur geänderte Dokumente werden neu verarbeitet
-   **Skalierbarkeit**: Fügen Sie weitere Worker hinzu, um den Durchsatz zu erhöhen

## 3. I/O Managers – Datenfluss zwischen Operationen

I/O Manager kümmern sich um das Laden von Inputs und das Speichern von Outputs für Assets. Sie agieren zwischen Operationen und verwalten die Datenpersistenz.

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

**Aufgaben eines I/O Managers:**

-   **Input-Laden**: Automatisches Abrufen von Daten aus Speichersystemen, bevor Operationen ausgeführt werden
-   **Output-Speichern**: Automatisches Speichern von Operationsergebnissen in geeigneten Speichern
-   **Typsicherheit**: Handhabung spezifischer Datentypen mit optimierter Serialisierung
-   **Speicherabstraktion**: Operationen müssen keine Details der Speicherimplementierung kennen
-   **Partitionsbewusstsein**: Verwendung von Partitionsschlüsseln zur Organisation der Datenspeicherung und -abfrage

## 4. Resources – Verwaltung externer Systeme

Resources stellen Konfiguration, Authentifizierung, Verbindungen und Operationen zu externen Systemen bereit.

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

**Aufgaben einer Resource:**

-   **Authentifizierung**: Handhabung von API-Schlüsseln, Verbindungszeichenfolgen und Anmeldeinformationen
-   **Konfiguration**: Bereitstellung von Einstellungen wie Timeouts, Wiederholungsversuchen und Endpunkten
-   **Verbindungsverwaltung**: Aufrechterhaltung von Datenbankverbindungen und Client-Instanzen
-   **Fehlerbehandlung**: Implementierung von Wiederholungslogik und Fehlerbehebung

## 5. Graph Assets – Zusammensetzen komplexer Operationen

Graph Assets sind Assets, die aus mehreren Operationen (Ops) bestehen, die zusammenarbeiten, um ein Endergebnis zu erzeugen.

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

**Eigenschaften von Graph Assets:**

-   **Operations-Komposition**: Verketten Sie mehrere Ops, um komplexe Verarbeitungen zu erstellen
-   **Wiederverwendbare Ops**: Einzelne Ops können über verschiedene Graph Assets hinweg wiederverwendet werden
-   **Klarer Datenfluss**: Jede Op empfängt typisierte Inputs und erzeugt typisierte Outputs
-   **Zwischenmaterialisierung**: Ops können Zwischenergebnisse für das Debugging speichern

## 6. Asset Factories – Wiederverwendbare Pipeline-Komponenten

Asset Factories sind Funktionen, die konfigurierte Assets erstellen und somit wiederverwendbare Pipeline-Komponenten ermöglichen.

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

**Vorteile von Asset Factories:**

-   **Wiederverwendbarkeit**: Dieselbe Factory kann Assets für verschiedene Umgebungen erstellen
-   **Parametrisierung**: Anpassen des Asset-Verhaltens durch Factory-Parameter
-   **Konsistenz**: Stellt sicher, dass Assets mit der richtigen Konfiguration erstellt werden
-   **Wartbarkeit**: Änderungen an der Asset-Logik müssen nur an einer Stelle vorgenommen werden

## 7. Resource Factory Pattern

Resource Factory-Funktionen erstellen vollständige Sätze von Resources für verschiedene Umgebungen und gewährleisten eine konsistente Konfiguration.

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

**Vorteile von Resource Factories:**

-   **Umgebungskonsistenz**: Derselbe Pipeline-Code funktioniert über Entwicklung/Test/Produktion hinweg
-   **Vollständige Konfiguration**: Alle zugehörigen Ressourcen werden zusammen konfiguriert
-   **Einfaches Umschalten**: Umgebungen können durch den Austausch von Factory-Funktionen gewechselt werden
-   **Keine Konfigurationsdrift**: Ressourcen werden immer konsistent konfiguriert

## Zusammenfassung der Muster

Diese Dagster-Muster arbeiten zusammen, um effiziente, wartbare Pipelines zu erstellen:

-   **Observable Assets**: Überwachen externe Datenquellen mithilfe von Inhaltshashes und Zeitstempeln
-   **Dynamic Partitions**: Verarbeiten jedes Dokument unabhängig für Fehlerisolation und Parallelität
-   **I/O Managers**: Handhaben die Datenpersistenz zwischen Operationen und Speichersystemen
-   **Resources**: Verwalten externe Systemverbindungen, Authentifizierung und Konfiguration
-   **Graph Assets**: Setzen komplexe Verarbeitungen aus wiederverwendbaren Operationen zusammen
-   **Asset Factories**: Erstellen konfigurierbare, wiederverwendbare Pipeline-Komponenten

## Was Sie gelernt haben

-   **Observable Assets**: Wie die Änderungserkennung mithilfe von Inhaltshashes und dynamischen Partitionen funktioniert
-   **I/O Managers**: Wie Daten zwischen Operationen und Speichersystemen fließen
-   **Resources**: Wie externe Systeme mit Authentifizierung und Konfiguration verwaltet werden
-   **Graph Assets**: Wie komplexe Operationen aus einfachen Bausteinen zusammengesetzt werden
-   **Asset Factories**: Wie wiederverwendbare, konfigurierbare Pipeline-Komponenten erstellt werden
-   **Resource Factories**: Wie umgebungsspezifische Konfigurationen verwaltet werden

## Nächste Schritte

-   [Daten-Ingestions-Pipeline](../2_data_ingestion_pipeline/) – Wenden Sie diese Muster auf eine funktionierende Pipeline an
