---
title: Ihre erste Pipeline
index: 4
source_sha: "5f923e4d73d088e745b3e08f7e9c29109c969fcc2fef2c66ed943576d72cf2e6"
---

# Ihre erste Pipeline

Bauen Sie Ihre erste Datenverarbeitungspipeline mit dem AI-Hub Pipeline (`aihub_pipeline`) SDK – eine vollständige Datentransformationspipeline mit mehreren verbundenen Assets.

## Was Sie lernen werden

Dieser Schnellstart behandelt die wesentlichen Bausteine:

- **Asset-Struktur**: Wie Pipelines Daten durch verbundene Assets verarbeiten
- **Datenfluss**: Wie Daten automatisch zwischen Assets fließen
- **Konfiguration**: Einstellungen und Ressourcen, die das Pipeline-Verhalten steuern
- **Testen**: Ausführen Ihrer Pipeline lokal und in der Dagster UI
- **Observability**: Überwachung der Pipeline-Ausführung mit integrierten Tools

## Voraussetzungen

Sie benötigen die laufende AI-Hub Entwicklungsumgebung. Bevor Sie beginnen, stellen Sie sicher, dass Sie die Schritte zur [Einrichtung der Entwicklungsumgebung](../1_dev_environment_setup/) abgeschlossen haben.

## Wie Pipelines funktionieren

AI-Hub Pipelines sind **Datenverarbeitungs-Workflows**, die auf Dagster basieren und aus drei wesentlichen Teilen bestehen:

- **Assets**: Funktionen, die Daten erstellen, transformieren oder konsumieren
- **Abhängigkeiten**: Automatischer Datenfluss zwischen Assets basierend auf Funktionsparametern
- **Ressourcen**: Gemeinsame Konfiguration und Dienste für externe Systeme

## Erstellen Sie Ihre erste Pipeline

Lassen Sie uns eine Datenpipeline erstellen, die Benutzer-Feedback-Daten verarbeitet.

### Beginnen Sie mit einer einfachen Pipeline

Zuerst wollen wir die Pipeline-Grundlagen anhand eines minimalen Beispiels verstehen:

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

- **Asset-Linien-Graph**: raw_feedback_data → cleaned_feedback
- **Materialisierungs-Buttons** zum Ausführen von Assets
- **Asset-Details**, die Inputs, Outputs und Ausführungslogs zeigen

Klicken Sie auf **„Materialize all“**, um die Pipeline auszuführen und den Datenfluss zu sehen!

## Eine echte AI-Hub Pipeline bauen

Lassen Sie uns nun eine realistische Pipeline mit dem `aihub_pipeline` SDK erstellen, die Dokumentverarbeitungsmuster demonstriert. Wir werden dies Schritt für Schritt aufschlüsseln, um jede Komponente zu verstehen.

### 1. Die AI-Hub Pipeline-Struktur verstehen

AI-Hub Pipelines folgen diesen Schlüsselmustern:

- **Asset Factories**: Wiederverwendbare Funktionen, die konfigurierte Assets erstellen
- **Ressourcen**: Konfigurierte Dienste wie Parser, Stores und Embedding-Modelle
- **Dynamische Partitionen**: Jedes Dokument wird zu einer separaten Partition für die parallele Verarbeitung

### 2. Konfigurieren Sie Ihre Pipeline

Beginnen Sie mit der Erstellung der grundlegenden Konfiguration und Imports (`my_document_pipeline.py`):

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
DATA_LAKE_KEY = AssetKey(["playground", "data_lake"])      # Rohdateispeicher 
DOCUMENT_KEY = AssetKey(["playground", "documents"])       # Analysierte Dokumente
NODES_KEY = AssetKey(["playground", "nodes"])              # Dokument-Chunks mit Embeddings

# Speicherkonfiguration
CONTAINER_NAME = "playground"    # S3 Bucket/Container-Name
DIRECTORY_NAME = "documents"     # Ordner für Dokumente
NAMESPACE_NAME = DIRECTORY_NAME  # Vektor-Store-Namespace
STORE_NAME = CONTAINER_NAME      # Dokument-Store-Name

# Dynamische Partitionen ermöglichen die parallele Verarbeitung einzelner Dokumente
document_partitions = DynamicPartitionsDefinition(name="document_partitions")
```

### 3. Erstellen Sie Ihre Pipeline-Assets

Als Nächstes erstellen Sie die drei Haupt-Assets, die Ihre Verarbeitungspipeline bilden:

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

**Die Asset-Factories verstehen:**

- `observable_data_lake_factory`: Erstellt ein Asset, das Dateiänderungen überwacht
- `documents_factory`: Erstellt ein Asset, das Dateien in RefDoc-Objekte mit Metadaten parst
- `nodes_factory`: Erstellt ein Asset, das Dokumente chunkt und Vektor-Embeddings generiert

### 4. Konfigurieren Sie Ihre Pipeline-Ressourcen

Konfigurieren Sie nun die Ressourcen (Dienste), die Ihre Pipeline benötigt:

```python
# Resource configuration - split into logical groups for clarity

# A. Speicher- und E/A-Ressourcen
storage_resources = {
    # Data Lake I/O Manager für S3-kompatiblen Speicher
    **default_io_manager_s3_datalake_resources(
        container_name=CONTAINER_NAME, 
        directory_name=DIRECTORY_NAME
    ),
    
    # Data Lake Ressourcen für die Dateiverwaltung
    **s3_data_lake_resources(
        container_name=CONTAINER_NAME,
        directory_name=DIRECTORY_NAME,
        figures_directory_name="__figures__",  # Für extrahierte Bilder/Abbildungen
    ),
}

# B. Dokumentenverarbeitungs-Ressourcen  
processing_resources = {
    # Dokument-Parser – verwendet KI-gestütztes Docling für PDF/Word/etc.
    "document_parser": DocumentParserResource(loader_type=LoaderType.DOCLING),
    
    # Node-Parser – chunkt Dokumente mithilfe struktureller Elemente  
    "node_parser": MarkdownStructuralNodeParserResource(),
}

# C. Datenbank- und Suchressourcen
database_resources = {
    # Vector Store und Document Store (MongoDB + Milvus)
    **local_mongo_milvus_storage_context_resource(
        vector_store_uri="http://localhost:19530",  # Milvus-Verbindung
        store_name=STORE_NAME,
        namespace_name=NAMESPACE_NAME,
    ),
}

# D. KI-Modell-Ressourcen
ai_resources = {
    # Embedding-Modell zum Erstellen von Vektorrepräsentationen
    "embedding_model": EmbeddingModelResource(
        embedding_config=EmbeddingModelConfig(
            model_name="azure/text-embedding-3-large"
        ),
    ),
}

# Alle Ressourcen kombinieren
all_resources = {
    **storage_resources,
    **processing_resources, 
    **database_resources,
    **ai_resources,
}
```

### 5. Definieren Sie Ihre vollständige Pipeline

Fassen Sie schließlich alles in der Pipeline-Definition zusammen:

```python
# Define the complete pipeline
defs = Definitions(
    assets=assets,           # Die drei Verarbeitungs-Assets
    resources=all_resources, # Alle konfigurierten Dienste
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

Sie werden die vollständige Dokumentenverarbeitungspipeline sehen:

```
data_lake (observable) → documents → nodes
                            ↓          ↓
                       (DocStore)  (VectorStore)
```

### 7. Den Datenfluss verstehen:

1.  **Observable Data Lake**: Überwacht neue PDF-, Word-, Markdown- usw. Dateien
2.  **Documents**: Parst Dateien mithilfe von KI-gestützter Dokumentenintelligenz (Docling)
3.  **Nodes**: Chunked Dokumente mittels strukturellem Parsing und generiert Embeddings

### 8. Fügen Sie Jobs und Scheduling zu Ihrer Pipeline hinzu

Für Produktions-Pipelines möchten Sie Jobs und Scheduling hinzufügen. Erweitern wir die Pipeline:

```python
# Add these imports to my_document_pipeline.py
from aihub_pipeline.jobs.factory import observe_source_job
from aihub_pipeline.schedules.factory import daily_schedule_at
from aihub_pipeline.sensors.factory import default_automation_sensor

# Jobs für verschiedene Operationen erstellen
observe_job = observe_source_job(
    observable_asset=observable_asset,
    namespace_name=NAMESPACE_NAME,
)

# Aktualisieren Sie Ihre Pipeline-Definition, um Jobs und Zeitpläne aufzunehmen
defs = Definitions(
    assets=assets,
    resources={
        # ... your existing resources ...
    },
    
    # Jobs für Pipeline-Operationen hinzufügen
    jobs=[observe_job],
    
    # Scheduling hinzufügen – täglich um Mitternacht beobachten
    schedules=[daily_schedule_at(observe_job, hour=0, minute=0)],
    
    # Sensoren für Automatisierung hinzufügen
    sensors=[default_automation_sensor(assets)],
)
```

**Jobs und Scheduling verstehen:**

-   **observe_job**: Manuelles Auslösen der Überwachung des Data Lakes
-   **daily_schedule_at**: Automatisches Data Lake-Monitoring planen
-   **default_automation_sensor**: Asset-Verarbeitung automatisch auslösen, wenn sich Abhängigkeiten ändern

Ihre Pipeline unterstützt nun:

-   **Manuelle Ausführung**: Einzelne Assets in der Dagster UI materialisieren
-   **Geplante Überwachung**: Tägliche Überprüfung auf neue Dokumente
-   **Automatische Verarbeitung**: Assets werden automatisch verarbeitet, wenn Upstream-Änderungen erkannt werden

### 9. Überwachen mit AI-Hub Observability Tools:

-   **Dagster UI** (`http://localhost:3000`): Asset-Linienherkunft, Ausführungslogs und Materialisierungsverlauf
-   **MinIO Konsole** (`http://localhost:9001`): Dateiverwaltung des Data Lakes
-   **MongoDB Compass**: Inspektion des Dokument-Stores
-   **Milvus (Attu)**: Überwachung der Vektor-Datenbank

### 10. AI-Hub Pipeline-Muster verstehen

Ihre AI-Hub Pipeline demonstriert Schlüsselmuster:

1.  **Observable Assets**: Erkennen neue Dokumente automatisch ohne manuelles Eingreifen
2.  **Dynamische Partitionen**: Jedes Dokument wird unabhängig verarbeitet
3.  **Ressourcenmanagement**: Konfigurierbare Parser, Modelle und Speicher-Backends
4.  **Automatisierungsrichtlinien**: Vorausschauende Verarbeitung bei Änderungen an Upstream-Assets

## Was Sie gelernt haben

-   **AI-Hub SDK Nutzung**: Verwendung von Factories, Ressourcen und typisierten Datenobjekten aus `aihub_pipeline`
-   **Dokumentenverarbeitungs-Pipeline**: Vollständiger Fluss von Rohdateien zu durchsuchbaren Embeddings
-   **Asset Factory Nutzung**: Verwendung bestehender Factories wie `documents_factory` und `nodes_factory`
-   **Ressourcenkonfiguration**: Einrichtung von Parsern, LLMs und Speichersystemen
-   **Observability**: Überwachung von KI-gestützten Pipelines mit Dagster
-   **Produktionsreife**: Skalierbare, automatisierte und wartbare Pipeline-Architektur

## Nächste Schritte

-   [Pipelines erstellen](../../3_building_pipelines/) – Lernen Sie fortgeschrittene AI-Hub Pipeline-Muster
