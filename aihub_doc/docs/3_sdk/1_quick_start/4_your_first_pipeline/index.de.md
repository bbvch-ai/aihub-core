---
title: Ihre erste Pipeline
source_sha: "9a11be49cd81ff051969e541e5e13a67ea7d757acc5cc5dee257d59c3da16d7d"
---

# Ihre erste Pipeline

Erstellen Sie Ihre erste Datenverarbeitungspipeline mithilfe des AI-Hub Pipeline (`aihub_pipeline`) SDK – eine vollständige Datentransformationspipeline mit mehreren verbundenen Assets.

## Was Sie lernen werden

Dieser Quickstart behandelt die wesentlichen Bausteine:

- **Asset-Struktur**: Wie Pipelines Daten durch verbundene Assets verarbeiten
- **Datenfluss**: Wie Daten automatisch zwischen Assets fließen
- **Konfiguration**: Einstellungen und Ressourcen, die das Pipeline-Verhalten steuern
- **Testen**: Ausführen Ihrer Pipeline lokal und in der Dagster UI
- **Observability**: Überwachung der Pipeline-Ausführung mit integrierten Tools

## Voraussetzungen

Sie benötigen eine laufende AI-Hub Entwicklungsumgebung. Bevor Sie beginnen, stellen Sie sicher, dass Sie die Schritte zur [Einrichtung der Entwicklungsumgebung](../1_dev_environment_setup/) abgeschlossen haben.

## Wie Pipelines funktionieren

AI-Hub Pipelines sind **Datenverarbeitungsworkflows**, die auf Dagster basieren und aus drei wesentlichen Teilen bestehen:

- **Assets**: Funktionen, die Daten erstellen, transformieren oder konsumieren
- **Abhängigkeiten**: Automatischer Datenfluss zwischen Assets basierend auf Funktionsparametern
- **Ressourcen**: Gemeinsam genutzte Konfigurationen und Services für externe Systeme

## Erstellen Sie Ihre erste Pipeline

Lassen Sie uns eine Datenpipeline erstellen, die Benutzer-Feedback-Daten verarbeitet.

### Beginnen Sie mit einer einfachen Pipeline

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

#### 3. Führen Sie Ihre einfache Pipeline aus:

```bash
poetry run dagster dev -f simple_pipeline.py
```

Öffnen Sie `http://localhost:3000` und Sie sehen:

- **Asset-Lineage-Graph**: raw_feedback_data → cleaned_feedback
- **Materialisieren-Buttons** zur Ausführung von Assets
- **Asset-Details**, die Inputs, Outputs und Ausführungslogs anzeigen

Klicken Sie auf **„Materialize all“**, um die Pipeline auszuführen und den Datenfluss zu sehen!

## Erstellen Sie eine echte AI-Hub Pipeline

Lassen Sie uns nun eine realistische Pipeline mit dem `aihub_pipeline` SDK erstellen, die Dokumentenverarbeitungsmuster demonstriert. Wir werden dies Schritt für Schritt aufschlüsseln, um jede Komponente zu verstehen.

### 1. Die AI-Hub Pipeline-Struktur verstehen

AI-Hub Pipelines folgen diesen Schlüsselmustern:

- **Asset Factories**: Wiederverwendbare Funktionen, die konfigurierte Assets erstellen
- **Ressourcen**: Konfigurierte Services wie Parser, Stores und Embedding-Modelle
- **Dynamische Partitionen**: Jedes Dokument wird zu einer separaten Partition für die parallele Verarbeitung

### 2. Richten Sie Ihre Pipeline-Konfiguration ein

Beginnen Sie mit der Erstellung der Basiskonfiguration und der Imports (`my_document_pipeline.py`):

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
DATA_LAKE_KEY = AssetKey(["playground", "data_lake"])      # Speicher für Rohdateien
DOCUMENT_KEY = AssetKey(["playground", "documents"])       # Geparsed Dokumente
NODES_KEY = AssetKey(["playground", "nodes"])              # Dokumenten-Chunks mit Embeddings

# Storage configuration
CONTAINER_NAME = "playground"    # S3 Bucket-/Container-Name
DIRECTORY_NAME = "documents"     # Ordner für Dokumente
NAMESPACE_NAME = DIRECTORY_NAME  # Vector-Store-Namespace
STORE_NAME = CONTAINER_NAME      # Dokumentenspeicher-Name

# Dynamische Partitionen ermöglichen die parallele Verarbeitung einzelner Dokumente
document_partitions = DynamicPartitionsDefinition(name="document_partitions")
```

### 3. Erstellen Sie Ihre Pipeline-Assets

Erstellen Sie als Nächstes die drei Haupt-Assets, die Ihre Verarbeitungspipeline bilden:

```python
# Erstellen Sie die Pipeline-Assets mithilfe von AI-Hub Factories

# 1. Observable Data Lake – überwacht neue/geänderte Dateien
observable_asset = observable_data_lake_factory(
    asset_key=DATA_LAKE_KEY, 
    partitions=document_partitions
)

# 2. Dokumente-Asset – verarbeitet Rohdateien in strukturierte Dokumente
documents_asset = documents_factory(
    asset_key=DOCUMENT_KEY,
    data_lake_key=DATA_LAKE_KEY,    # Hängt vom Data Lake ab
    partitions=document_partitions   # Eine Partition pro Dokument
)

# 3. Nodes-Asset – zerlegt Dokumente in Chunks und erstellt Embeddings
nodes_asset = nodes_factory(
    asset_key=NODES_KEY,
    document_key=DOCUMENT_KEY,       # Hängt von Dokumenten ab
    partitions=document_partitions   # Eine Partition pro Dokument
)

# Alle Assets kombinieren
assets = [observable_asset, documents_asset, nodes_asset]
```

**Die Asset Factories verstehen:**

- `observable_data_lake_factory`: Erstellt ein Asset, das Dateiänderungen überwacht
- `documents_factory`: Erstellt ein Asset, das Dateien in RefDoc-Objekte mit Metadaten parst
- `nodes_factory`: Erstellt ein Asset, das Dokumente zerlegt und Vektor-Embeddings generiert

### 4. Konfigurieren Sie Ihre Pipeline-Ressourcen

Konfigurieren Sie nun die Ressourcen (Services), die Ihre Pipeline benötigt:

```python
# Ressourcenkonfiguration – zur besseren Übersichtlichkeit in logische Gruppen unterteilt

# A. Speicher- und I/O-Ressourcen
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

# B. Dokumentenverarbeitungsressourcen  
processing_resources = {
    # Dokumenten-Parser – verwendet KI-gestütztes Docling für PDF/Word/etc.
    "document_parser": DocumentParserResource(loader_type=LoaderType.DOCLING),
    
    # Node-Parser – zerlegt Dokumente mithilfe struktureller Elemente  
    "node_parser": MarkdownStructuralNodeParserResource(),
}

# C. Datenbank- und Suchressourcen
database_resources = {
    # Vector Store und Dokumentenspeicher (MongoDB + Milvus)
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

### 5. Definieren Sie Ihre komplette Pipeline

Führen Sie abschließend alles in der Pipeline-Definition zusammen:

```python
# Definieren Sie die komplette Pipeline
defs = Definitions(
    assets=assets,           # Die drei Verarbeitungs-Assets
    resources=all_resources, # Alle konfigurierten Services
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

Sie sehen die vollständige Dokumentenverarbeitungspipeline:

```
data_lake (observable) → documents → nodes
                            ↓          ↓
                       (DocStore)  (VectorStore)
```

### 7. Den Datenfluss verstehen:

1. **Observable Data Lake**: Überwacht neue PDF-, Word-, Markdown- usw. Dateien
2. **Documents**: Parsed Dateien mithilfe von KI-gestützter Dokumentenintelligenz (Docling)
3. **Nodes**: Zerlegt Dokumente mithilfe struktureller Analyse und generiert Embeddings

### 8. Fügen Sie Ihrer Pipeline Jobs und Zeitplanung hinzu

Für Produktions-Pipelines möchten Sie Jobs und Zeitplanung hinzufügen. Erweitern wir die Pipeline:

```python
# Add these imports to my_document_pipeline.py
from aihub_pipeline.jobs.factory import observe_source_job
from aihub_pipeline.schedules.factory import daily_schedule_at
from aihub_pipeline.sensors.factory import default_automation_sensor

# Erstellen Sie Jobs für verschiedene Operationen
observe_job = observe_source_job(
    observable_asset=observable_asset,
    namespace_name=NAMESPACE_NAME,
)

# Aktualisieren Sie Ihre Pipeline-Definition, um Jobs und Zeitpläne einzuschließen
defs = Definitions(
    assets=assets,
    resources={
        # ... Ihre bestehenden Ressourcen ...
    },
    
    # Fügen Sie Jobs für Pipeline-Operationen hinzu
    jobs=[observe_job],
    
    # Fügen Sie Zeitplanung hinzu – tägliche Beobachtung um Mitternacht
    schedules=[daily_schedule_at(observe_job, hour=0, minute=0)],
    
    # Fügen Sie Sensoren für die Automatisierung hinzu
    sensors=[default_automation_sensor(assets)],
)
```

**Jobs und Zeitplanung verstehen:**

- **observe_job**: Manuelles Auslösen der Beobachtung des Data Lakes
- **daily_schedule_at**: Zeitplanung der automatischen Data Lake Beobachtung
- **default_automation_sensor**: Automatisches Auslösen der Asset-Verarbeitung bei Änderungen der Abhängigkeiten

Ihre Pipeline unterstützt nun:

- **Manuelle Ausführung**: Materialisieren einzelner Assets in der Dagster UI
- **Geplante Beobachtung**: Tägliche Überprüfung auf neue Dokumente
- **Automatische Verarbeitung**: Assets werden automatisch verarbeitet, wenn Upstream-Änderungen erkannt werden

### 9. Überwachung mit AI-Hub Observability Tools:

- **Dagster UI** (`http://localhost:3000`): Asset-Lineage, Ausführungslogs und Materialisierungs-Historie
- **MongoDB Compass**: Inspektion des Dokumentenspeichers
- **Milvus (Attu)**: Überwachung der Vektordatenbank

::: tip SeaweedFS Filer
In Produktion ist die SeaweedFS Filer Web-UI unter `datalake.${DOMAIN}` zugänglich (OAuth2 geschützt, erfordert die Rolle AIHubDeveloper).
Im Entwicklungsmodus ist sie unter `http://localhost:8889` zum Durchsuchen hochgeladener Dateien und zum Debuggen des Speichers verfügbar.
:::

### 10. AI-Hub Pipeline-Muster verstehen

Ihre AI-Hub Pipeline demonstriert Schlüsselmuster:

1. **Observable Assets**: Erkennen neue Dokumente automatisch ohne manuelles Eingreifen
2. **Dynamische Partitionen**: Jedes Dokument wird unabhängig verarbeitet
3. **Ressourcenmanagement**: Konfigurierbare Parser, Modelle und Speicher-Backends
4. **Automatisierungsrichtlinien**: Eifrige Verarbeitung, wenn Upstream-Assets sich ändern

## Was Sie gelernt haben

- **AI-Hub SDK Nutzung**: Verwendung von Factories, Ressourcen und typisierten Datenobjekten aus `aihub_pipeline`
- **Dokumentenverarbeitungspipeline**: Vollständiger Fluss von Rohdateien zu durchsuchbaren Embeddings
- **Asset Factory Nutzung**: Verwendung bestehender Factories wie `documents_factory` und `nodes_factory`
- **Ressourcenkonfiguration**: Einrichtung von Parsers, LLMs und Speichersystemen
- **Observability**: Überwachung von KI-gestützten Pipelines mit Dagster
- **Produktionsreife**: Skalierbare, automatisierte und wartbare Pipeline-Architektur

## Nächste Schritte

- [Pipelines erstellen](../../3_building_pipelines/) – Lernen Sie fortgeschrittene AI-Hub Pipeline-Muster
