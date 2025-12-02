---
title: Ihre erste Pipeline
source_sha: "6eda40232df66fb120c07693f0756ad958b67fe6005350780b4f3613db96805c"
---

# Ihre erste Pipeline

Erstellen Sie Ihre erste Datenverarbeitungs-Pipeline mit dem AI-Hub Pipeline (`aihub_pipeline`) SDK – eine vollständige Datentransformations-Pipeline mit mehreren verbundenen Assets.

## Was Sie lernen werden

Dieser Quickstart behandelt die wesentlichen Bausteine:

- **Asset-Struktur**: Wie Pipelines Daten durch verbundene Assets verarbeiten
- **Datenfluss**: Wie Daten automatisch zwischen Assets fließen
- **Konfiguration**: Einstellungen und Ressourcen, die das Pipeline-Verhalten steuern
- **Testing**: Ihre Pipeline lokal und in der Dagster UI ausführen
- **Observability**: Überwachung der Pipeline-Ausführung mit integrierten Tools

## Voraussetzungen

Sie benötigen eine laufende AI-Hub Entwicklungsumgebung. Bevor Sie beginnen, stellen Sie sicher, dass Sie die Schritte zum [Einrichten der Entwicklungsumgebung](../1_dev_environment_setup/) abgeschlossen haben.

## Wie Pipelines funktionieren

AI-Hub Pipelines sind **Datenverarbeitungs-Workflows**, die auf Dagster basieren und drei wesentliche Bestandteile haben:

- **Assets**: Funktionen, die Daten erstellen, transformieren oder konsumieren
- **Dependencies**: Automatischer Datenfluss zwischen Assets basierend auf Funktionsparametern
- **Resources**: Gemeinsam genutzte Konfigurationen und Services für externe Systeme

## Erstellen Sie Ihre erste Pipeline

Lassen Sie uns eine Datenpipeline erstellen, die Benutzerfeedback-Daten verarbeitet.

### Beginnen Sie mit einer einfachen Pipeline

Lassen Sie uns zunächst die Grundlagen von Pipelines anhand eines minimalen Beispiels verstehen:

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

Öffnen Sie `http://localhost:3000` und Sie sehen:

- **Asset Lineage Graph**: raw_feedback_data → cleaned_feedback
- **Materialize Buttons** zum Ausführen von Assets
- **Asset Details** mit Eingaben, Ausgaben und Ausführungsprotokollen

Klicken Sie auf **"Materialize all"**, um die Pipeline auszuführen und den Datenfluss zu sehen!

## Erstellen Sie eine echte AI-Hub Pipeline

Lassen Sie uns nun eine realistische Pipeline mit dem `aihub_pipeline` SDK erstellen, die Dokumentenverarbeitungsmuster demonstriert. Wir werden dies Schritt für Schritt aufschlüsseln, um jede Komponente zu verstehen.

### 1. Verständnis der AI-Hub Pipeline-Struktur

AI-Hub Pipelines folgen diesen Schlüsselmustern:

- **Asset Factories**: Wiederverwendbare Funktionen, die konfigurierte Assets erstellen
- **Resources**: Konfigurierte Services wie Parser, Stores und Embedding-Modelle
- **Dynamic Partitions**: Jedes Dokument wird zu einer separaten Partition für die parallele Verarbeitung

### 2. Richten Sie Ihre Pipeline-Konfiguration ein

Beginnen Sie mit der Erstellung der Basiskonfiguration und der Importe (`my_document_pipeline.py`):

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

Als Nächstes erstellen Sie die drei Haupt-Assets, die Ihre Verarbeitungs-Pipeline bilden:

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

- `observable_data_lake_factory`: Erstellt ein Asset, das Dateiänderungen überwacht
- `documents_factory`: Erstellt ein Asset, das Dateien in RefDoc-Objekte mit Metadaten parst
- `nodes_factory`: Erstellt ein Asset, das Dokumente chunkt und Vektor-Embeddings generiert

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
    # Document parser - uses AI-powered Docling for PDF/Word/etc
    "document_parser": DocumentParserResource(loader_type=LoaderType.DOCLING),
    
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

### 5. Definieren Sie Ihre komplette Pipeline

Führen Sie schließlich alles in der Pipeline-Definition zusammen:

```python
# Define the complete pipeline
defs = Definitions(
    assets=assets,           # The three processing assets
    resources=all_resources, # All configured services
)
```

**Komplette Pipeline-Datei** (`my_document_pipeline.py`):

Hier ist die komplette Datei mit allen Komponenten zusammen:

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
        "document_parser": DocumentParserResource(loader_type=LoaderType.DOCLING),
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

Sie werden die komplette Dokumentenverarbeitungs-Pipeline sehen:

```
data_lake (observable) → documents → nodes
                            ↓          ↓
                       (DocStore)  (VectorStore)
```

### 7. Verständnis des Datenflusses:

1. **Observable Data Lake**: Überwacht neue PDF-, Word-, Markdown- usw. Dateien
2. **Documents**: Parst Dateien mithilfe KI-gestützter Dokumentenintelligenz (Docling)
3. **Nodes**: Chunked Dokumente mithilfe strukturellem Parsing und generiert Embeddings

### 8. Fügen Sie Jobs und Scheduling zu Ihrer Pipeline hinzu

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

- **observe_job**: Manuelles Auslösen der Beobachtung des Data Lakes
- **daily_schedule_at**: Planen der automatischen Data Lake-Beobachtung
- **default_automation_sensor**: Automatisches Auslösen der Asset-Verarbeitung bei Änderungen der Abhängigkeiten

Ihre Pipeline unterstützt nun:

- **Manuelle Ausführung**: Materialisieren einzelner Assets in der Dagster UI
- **Geplante Beobachtung**: Tägliche Überprüfung auf neue Dokumente
- **Automatische Verarbeitung**: Assets werden automatisch verarbeitet, wenn Upstream-Änderungen erkannt werden

### 9. Überwachung mit AI-Hub Observability-Tools:

- **Dagster UI** (`http://localhost:3000`): Asset Lineage, Ausführungsprotokolle und Materialisierungs-Historie
- **MongoDB Compass**: Inspektion des Dokumentenspeichers
- **Milvus (Attu)**: Überwachung der Vektordatenbank

::: tip SeaweedFS Filer
Die SeaweedFS Filer Web UI ist nur intern verfügbar und nicht extern zugänglich. Die Dateiverwaltung erfolgt über die S3 API.
:::

### 10. Verständnis der AI-Hub Pipeline-Muster

Ihre AI-Hub Pipeline demonstriert Schlüsselmuster:

1. **Observable Assets**: Erkennen neue Dokumente automatisch ohne manuelles Eingreifen
2. **Dynamic Partitions**: Jedes Dokument wird unabhängig voneinander verarbeitet
3. **Resource Management**: Konfigurierbare Parser, Modelle und Storage Backends
4. **Automation Policies**: Eager Processing, wenn Upstream-Assets sich ändern

## Was Sie gelernt haben

- **AI-Hub SDK Nutzung**: Verwendung von Factories, Ressourcen und typisierten Datenobjekten aus `aihub_pipeline`
- **Dokumentenverarbeitungs-Pipeline**: Kompletter Flow von Rohdateien zu durchsuchbaren Embeddings
- **Asset Factory Nutzung**: Verwendung bestehender Factories wie `documents_factory` und `nodes_factory`
- **Ressourcenkonfiguration**: Einrichten von Parsern, LLMs und Speichersystemen
- **Observability**: Überwachung von KI-gestützten Pipelines mit Dagster
- **Produktionsreife**: Skalierbare, automatisierte und wartbare Pipeline-Architektur

## Nächste Schritte

- [Pipelines erstellen](../../3_building_pipelines/) – Erfahren Sie mehr über fortgeschrittene AI-Hub Pipeline-Muster
