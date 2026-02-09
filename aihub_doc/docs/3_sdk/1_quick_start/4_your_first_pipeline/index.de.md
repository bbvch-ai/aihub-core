---
title: Ihre erste Pipeline
source_sha: "c2f2e23557008f5a3233763f6e0cf76edbb84ec23db85dfdba9281767245d5c1"
---

# Ihre erste Pipeline

Erstellen Sie Ihre erste Datenverarbeitungs-Pipeline mit dem AI-Hub Pipeline (`aihub_pipeline`) SDK – einer vollständigen Datentransformations-Pipeline mit mehreren verbundenen Assets.

## Was Sie lernen werden

Dieser Quickstart behandelt die wesentlichen Bausteine:

- **Asset-Struktur**: Wie Pipelines Daten durch verbundene Assets verarbeiten
- **Datenfluss**: Wie Daten automatisch zwischen Assets fließen
- **Konfiguration**: Einstellungen und Ressourcen, die das Pipeline-Verhalten steuern
- **Testen**: Ausführen Ihrer Pipeline lokal und in der Dagster UI
- **Observability**: Überwachung der Pipeline-Ausführung mit integrierten Tools

## Voraussetzungen

Sie benötigen die AI-Hub Entwicklungsumgebung. Bevor Sie beginnen, stellen Sie sicher, dass Sie die Schritte zur [Einrichtung der Entwicklungsumgebung](../1_dev_environment_setup/) abgeschlossen haben.

## Wie Pipelines funktionieren

AI-Hub Pipelines sind **Datenverarbeitungs-Workflows**, die auf Dagster basieren und aus drei wesentlichen Teilen bestehen:

- **Assets**: Funktionen, die Daten erstellen, transformieren oder konsumieren
- **Abhängigkeiten**: Automatischer Datenfluss zwischen Assets basierend auf Funktionsparametern
- **Ressourcen**: Geteilte Konfiguration und Services für externe Systeme

## Erstellen Sie Ihre erste Pipeline

Lassen Sie uns eine Daten-Pipeline erstellen, die Benutzer-Feedback-Daten verarbeitet.

### Starten Sie mit einer einfachen Pipeline

Lassen Sie uns zunächst die Grundlagen einer Pipeline an einem minimalen Beispiel verstehen:

#### 1. Erstellen Sie Ihre grundlegenden Assets (`simple_pipeline.py`):

```python
from dagster import AssetExecutionContext, Output, asset


@asset(description="Raw text data source")
def raw_feedback_data(context: AssetExecutionContext) -> Output[str]:
    """Source asset that provides raw user feedback data."""
    feedback = "The product is amazing but the documentation could be better!"
    context.log.info(f"Loaded raw feedback: {feedback}")
    return Output(feedback, metadata={"feedback": feedback})


@asset(description="Cleaned and processed feedback")
def cleaned_feedback(context: AssetExecutionContext, raw_feedback_data: str) -> Output[dict]:
    """Transform raw feedback into structured data."""
    # Simple processing: clean text and extract basic metrics
    text = raw_feedback_data.strip().lower()
    words = text.split()

    processed = {
        "original_text": raw_feedback_data,
        "cleaned_text": text,
        "word_count": len(words),
        "sentiment": "positive" if "amazing" in text else "neutral",
    }

    context.log.info(f"Processed feedback: {processed}")
    return Output(
        processed,
        metadata={
            "original_text": processed["original_text"],
            "cleaned_text": processed["cleaned_text"],
            "word_count": processed["word_count"],
            "sentiment": processed["sentiment"],
        },
    )
```

#### 2. Fügen Sie die Pipeline-Definition hinzu (`simple_pipeline.py`):

```python
from dagster import Definitions

## ... your asset definitions from above ...

# Basic pipeline definition
defs = Definitions(assets=[raw_feedback_data, cleaned_feedback])
```

#### 3. Führen Sie Ihre grundlegende Pipeline aus:

```bash
poetry run dagster dev -f simple_pipeline.py
```

Öffnen Sie `http://localhost:3000`, und Sie werden Folgendes sehen:

- **Asset-Abstammungsgraph**: raw_feedback_data → cleaned_feedback
- **Materialize-Buttons**, um Assets auszuführen
- **Asset-Details**, die Eingaben, Ausgaben und Ausführungsprotokolle anzeigen

Klicken Sie auf **„Materialize all“**, um die Pipeline auszuführen und den Datenfluss zu sehen!

## Erstellen Sie eine echte AI-Hub Pipeline

Lassen Sie uns nun eine realistische Pipeline mithilfe des `aihub_pipeline` SDK erstellen, die Dokumentverarbeitungsmuster demonstriert. Wir werden dies Schritt für Schritt aufschlüsseln, um jede Komponente zu verstehen.

### 1. Verständnis der AI-Hub Pipeline-Struktur

AI-Hub Pipelines folgen diesen Schlüsselmustern:

- **Asset Factories**: Wiederverwendbare Funktionen, die konfigurierte Assets erstellen
- **Ressourcen**: Konfigurierte Services wie Parser, Stores und Embedding-Modelle
- **Dynamische Partitionen**: Jedes Dokument wird zu einer separaten Partition für die parallele Verarbeitung

### 2. Richten Sie Ihre Pipeline-Konfiguration ein

Beginnen Sie mit der Erstellung der grundlegenden Konfiguration und Importe (`my_document_pipeline.py`):

```python
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from dagster import AssetKey, AssetSelection, Definitions, DynamicPartitionsDefinition

# Import AI-Hub pipeline factories
from aihub_pipeline.assets.factories.data_lake_to_vector_store.documents_factory import documents_factory
from aihub_pipeline.assets.factories.data_lake_to_vector_store.nodes_factory import nodes_factory
from aihub_pipeline.assets.factories.data_lake_to_vector_store.observable_data_lake_factory import (
    observable_data_lake_factory,
)

# Import AI-Hub resources and utilities
from aihub_pipeline.resources.factory import (
    default_io_manager_s3_datalake_resources,
    local_mongo_milvus_storage_context_resource,
    s3_data_lake_resources,
)
from aihub_pipeline.resources.llm.EmbeddingModelResource import EmbeddingModelResource
from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource, LoaderType
from aihub_pipeline.resources.parser.MarkdownStructuralNodeParserResource import MarkdownStructuralNodeParserResource

# Pipeline configuration - defines where data flows between assets
DATA_LAKE_KEY = AssetKey(["playground", "data_lake"])      # Raw file storage 
DOCUMENT_KEY = AssetKey(["playground", "documents"])       # Parsed documents
NODES_KEY = AssetKey(["playground", "nodes"])              # Document chunks with embeddings

# Storage configuration
CONTAINER_NAME = "playground"    # S3 bucket/container name
DIRECTORY_NAME = "documents"     # Folder for documents
NAMESPACE_NAME = DIRECTORY_NAME  # Vector store namespace
STORE_NAME = CONTAINER_NAME      # Document store name

# Dynamic partitions allow parallel processing of individual documents
document_partitions = DynamicPartitionsDefinition(name="document_partitions")
```

### 3. Erstellen Sie Ihre Pipeline-Assets

Erstellen Sie als Nächstes die drei Haupt-Assets, die Ihre Verarbeitungs-Pipeline bilden:

```python
# Create the pipeline assets using AI-Hub factories

# 1. Observable Data Lake - watches for new/changed files
observable_asset = observable_data_lake_factory(
    asset_key=DATA_LAKE_KEY, 
    partitions=document_partitions
)

# 2. Documents Asset - processes raw files into structured documents
documents_asset = documents_factory(
    asset_key=DOCUMENT_KEY,
    data_lake_key=DATA_LAKE_KEY,    # Depends on data lake 
    partitions=document_partitions   # One partition per document
)

# 3. Nodes Asset - chunks documents and creates embeddings
nodes_asset = nodes_factory(
    asset_key=NODES_KEY,
    document_key=DOCUMENT_KEY,       # Depends on documents
    partitions=document_partitions   # One partition per document
)

# Combine all assets
assets = [observable_asset, documents_asset, nodes_asset]
```

**Verständnis der Asset Factories:**

- ``observable_data_lake_factory``: Erstellt ein Asset, das Dateiänderungen überwacht
- ``documents_factory``: Erstellt ein Asset, das Dateien in RefDoc-Objekte mit Metadaten parst
- ``nodes_factory``: Erstellt ein Asset, das Dokumente in Chunks zerlegt und Vektor-Embeddings generiert

### 4. Konfigurieren Sie Ihre Pipeline-Ressourcen

Konfigurieren Sie nun die Ressourcen (Services), die Ihre Pipeline benötigt:

```python
# Resource configuration - split into logical groups for clarity

# A. Storage and I/O Resources
storage_resources = {
    # Data lake I/O managers for S3-compatible storage
    **default_io_manager_s3_datalake_resources(
        container_name=CONTAINER_NAME, 
        directory_name=DIRECTORY_NAME
    ),
    
    # Data lake resources for file management
    **s3_data_lake_resources(
        container_name=CONTAINER_NAME,
        directory_name=DIRECTORY_NAME,
        figures_directory_name="__figures__",  # For extracted images/figures
    ),
}

# B. Document Processing Resources  
processing_resources = {
    # Document parser - uses AI-powered MinerU for PDF/Word/etc
    "document_parser": DocumentParserResource(loader_type=LoaderType.MINERU),

    # Node parser - chunks documents using structural elements
    "node_parser": MarkdownStructuralNodeParserResource(),
}

# C. Database and Search Resources
database_resources = {
    # Vector store and document store (MongoDB + Milvus)
    **local_mongo_milvus_storage_context_resource(
        vector_store_uri="http://localhost:19530",  # Milvus connection
        store_name=STORE_NAME,
        namespace_name=NAMESPACE_NAME,
    ),
}

# D. AI Model Resources
ai_resources = {
    # Embedding model for creating vector representations
    "embedding_model": EmbeddingModelResource(
        embedding_config=EmbeddingModelConfig(
            model_name="azure/text-embedding-3-large"
        ),
    ),
}

# Combine all resources
all_resources = {
    **storage_resources,
    **processing_resources, 
    **database_resources,
    **ai_resources,
}
```

### 5. Definieren Sie Ihre vollständige Pipeline

Führen Sie abschließend alles in der Pipeline-Definition zusammen:

```python
# Define the complete pipeline
defs = Definitions(
    assets=assets,           # The three processing assets
    resources=all_resources, # All configured services
)
```

**Vollständige Pipeline-Datei** (`my_document_pipeline.py`):

Hier ist die vollständige Datei mit allen Komponenten zusammen:

```python
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from dagster import AssetKey, Definitions, DynamicPartitionsDefinition

from aihub_pipeline.assets.factories.data_lake_to_vector_store.documents_factory import documents_factory
from aihub_pipeline.assets.factories.data_lake_to_vector_store.nodes_factory import nodes_factory
from aihub_pipeline.assets.factories.data_lake_to_vector_store.observable_data_lake_factory import (
    observable_data_lake_factory,
)

from aihub_pipeline.resources.factory import (
    default_io_manager_s3_datalake_resources,
    local_mongo_milvus_storage_context_resource,
    s3_data_lake_resources,
)
from aihub_pipeline.resources.llm.EmbeddingModelResource import EmbeddingModelResource
from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource, LoaderType
from aihub_pipeline.resources.parser.MarkdownStructuralNodeParserResource import MarkdownStructuralNodeParserResource

# Configuration
DATA_LAKE_KEY = AssetKey(["playground", "data_lake"])
DOCUMENT_KEY = AssetKey(["playground", "documents"])  
NODES_KEY = AssetKey(["playground", "nodes"])

CONTAINER_NAME = "playground"
DIRECTORY_NAME = "documents" 
NAMESPACE_NAME = DIRECTORY_NAME
STORE_NAME = CONTAINER_NAME

document_partitions = DynamicPartitionsDefinition(name="document_partitions")

# Assets
observable_asset = observable_data_lake_factory(DATA_LAKE_KEY, document_partitions)
documents_asset = documents_factory(DOCUMENT_KEY, data_lake_key=DATA_LAKE_KEY, partitions=document_partitions)
nodes_asset = nodes_factory(NODES_KEY, document_key=DOCUMENT_KEY, partitions=document_partitions)

assets = [observable_asset, documents_asset, nodes_asset]

# Resources
defs = Definitions(
    assets=assets,
    resources={
        **default_io_manager_s3_datalake_resources(CONTAINER_NAME, DIRECTORY_NAME),
        **s3_data_lake_resources(CONTAINER_NAME, DIRECTORY_NAME, "__figures__"),
        **local_mongo_milvus_storage_context_resource("http://localhost:19530", STORE_NAME, NAMESPACE_NAME),
        "document_parser": DocumentParserResource(loader_type=LoaderType.MINERU),
        "node_parser": MarkdownStructuralNodeParserResource(),
        "embedding_model": EmbeddingModelResource(
            embedding_config=EmbeddingModelConfig(model_name="azure/text-embedding-3-large")
        ),
    },
)
```

### 6. Führen Sie Ihre AI-Hub Pipeline aus:

```bash
poetry run dagster dev -f my_document_pipeline.py
```

Sie sehen die vollständige Dokumentverarbeitungs-Pipeline:

```
data_lake (observable) → documents → nodes
                            ↓          ↓
                       (DocStore)  (VectorStore)
```

### 7. Verständnis des Datenflusses:

1. **Observable Data Lake**: Überwacht neue PDF-, Word-, Markdown- usw. Dateien
2. **Dokumente**: Parst Dateien mithilfe von KI-gestützter Dokumentenintelligenz (MinerU)
3. **Nodes**: Zerlegt Dokumente mithilfe struktureller Analyse und generiert Embeddings

### 8. Fügen Sie Ihrer Pipeline Jobs und Scheduling hinzu

Für Produktions-Pipelines möchten Sie Jobs und Scheduling hinzufügen. Erweitern wir die Pipeline:

```python
# Add these imports to my_document_pipeline.py
from aihub_pipeline.jobs.factory import observe_source_job
from aihub_pipeline.schedules.factory import daily_schedule_at
from aihub_pipeline.sensors.factory import default_automation_sensor

# Create jobs for different operations
observe_job = observe_source_job(
    observable_asset=observable_asset,
    namespace_name=NAMESPACE_NAME,
)

# Update your pipeline definition to include jobs and schedules
defs = Definitions(
    assets=assets,
    resources={
        # ... your existing resources ...
    },
    
    # Add jobs for pipeline operations
    jobs=[observe_job],
    
    # Add scheduling - observe daily at midnight
    schedules=[daily_schedule_at(observe_job, hour=0, minute=0)],
    
    # Add sensors for automation
    sensors=[default_automation_sensor(assets)],
)
```

**Verständnis von Jobs und Scheduling:**

- ``observe_job``: Manuelles Auslösen der Überwachung des Data Lake
- ``daily_schedule_at``: Automatisches Data-Lake-Monitoring planen
- ``default_automation_sensor``: Automatische Auslösung der Asset-Verarbeitung bei Abhängigkeitsänderungen

Ihre Pipeline unterstützt nun:

- **Manuelle Ausführung**: Individualisierte Assets in der Dagster UI materialisieren
- **Geplantes Monitoring**: Tägliche Überprüfung auf neue Dokumente
- **Automatische Verarbeitung**: Assets werden automatisch verarbeitet, wenn Upstream-Änderungen erkannt werden

### 9. Überwachen Sie mit AI-Hub Observability-Tools:

- **Dagster UI** (`http://localhost:3000`): Asset-Abstammung, Ausführungsprotokolle und Materialisierungshistorie
- **MongoDB Compass**: Inspektion des Dokument-Stores
- **Milvus (Attu)**: Monitoring der Vektor-Datenbank

::: Tipp SeaweedFS Filer
In der Produktion ist die SeaweedFS Filer Web-UI unter `datalake.${DOMAIN}` zugänglich (OAuth2 geschützt, erfordert die Rolle AIHubDeveloper). Im Entwicklungsmodus ist sie unter `http://localhost:8889` verfügbar, um hochgeladene Dateien zu durchsuchen und den Speicher zu debuggen.
:::

### 10. Verständnis der AI-Hub Pipeline-Muster

Ihre AI-Hub Pipeline demonstriert Schlüsselmuster:

1. **Observable Assets**: Automatische Erkennung neuer Dokumente ohne manuelles Eingreifen
2. **Dynamische Partitionen**: Jedes Dokument wird unabhängig verarbeitet
3. **Ressourcenmanagement**: Konfigurierbare Parser, Modelle und Speicher-Backends
4. **Automatisierungsrichtlinien**: Eifrige Verarbeitung bei Änderungen an Upstream-Assets

## Was Sie gelernt haben

- **Nutzung des AI-Hub SDK**: Verwendung von Factories, Ressourcen und typisierten Datenobjekten aus `aihub_pipeline`
- **Dokumentverarbeitungs-Pipeline**: Vollständiger Fluss von Rohdateien zu durchsuchbaren Embeddings
- **Nutzung von Asset Factories**: Verwendung bestehender Factories wie `documents_factory` und `nodes_factory`
- **Ressourcenkonfiguration**: Einrichtung von Parsern, LLMs und Speichersystemen
- **Observability**: Monitoring KI-gestützter Pipelines mit Dagster
- **Produktionsreife**: Skalierbare, automatisierte und wartbare Pipeline-Architektur

## Nächste Schritte

- [Pipelines erstellen](../../3_building_pipelines/)
