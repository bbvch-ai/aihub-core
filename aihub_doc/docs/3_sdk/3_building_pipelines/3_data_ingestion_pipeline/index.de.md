---
title: Datenaufnahme-Pipeline
source_sha: 64a6c3e202f73665c96754a7a24a73d2b027535986c61e72eaafe46955bb4d1a
---

# Datenaufnahme-Pipeline

Das AI-Hub Pipeline SDK bietet vorgefertigte, produktionsreife Pipeline-Definitionen, die Sie mit minimaler
Konfiguration verwenden können. Diese **Factories** kapseln Best Practices für die Aufnahme von Dokumenten und deren
Vorbereitung für RAG-Anwendungen.

## Die zweistufige Aufnahme-Architektur

Unser Aufnahmeprozess ist in zwei separate Phasen unterteilt, von denen jede von ihrer eigenen
Pipeline-Definitions-Factory gehandhabt wird. Dies fördert Modularität und Wiederverwendbarkeit.

1. **Phase 1: Quelle zum Data Lake** (Optional): Diese Pipeline verbindet sich mit einer externen Quelle (wie
   SharePoint) und synchronisiert ihre Dateien mit einem zentralen S3 Data Lake.
2. **Phase 2: Data Lake zum Vektor-Store**: Diese Pipeline überwacht den S3 Data Lake, verarbeitet die Dokumente und
   speichert die resultierenden Embeddings in einem Vektor-Store.

```mermaid
graph TD
    subgraph "Source Systems"
        A[SharePoint Sites]
        B[Confluence Wiki]
        C[Jira Projects]
        D[Manual Uploads]
        E[File Systems]
        F[Other Sources]
    end
    
    subgraph "Pipeline"
        G(Data Lake)
        H[Document Parsing]
        I(Document Store)
        J[Vector Embedding]
        K(Vector Store)
    end
    
    subgraph "Consumption"
        L(RAG Agents)
    end
    
    A --> G
    B --> G
    C --> G
    D --> G
    E --> G
    F --> G
    
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    
    style G fill:#3a5ccc
    style I fill:#7e4cc9
    style K fill:#299764
```

## 1. Die SharePoint-zu-Data-Lake-Pipeline

Verwenden Sie die `default_sharepoint_to_datalake_definitions` Factory, um Dokumente von einer SharePoint-Site mit Ihrem
S3 Data Lake zu synchronisieren.

- **Was es tut**: Beobachtet einen SharePoint-Speicherort, lädt neue oder aktualisierte Dateien herunter und bereinigt
  Dateien im Data Lake, die aus SharePoint gelöscht wurden.
- **Schlüssel-Assets**: `observable_sharepoint`, `data_lake_files`, `removed_data_lake_files`.

### Anwendungsbeispiel

```python
from aihub_pipeline.util.definitions_util import default_sharepoint_to_datalake_definitions

defs = default_sharepoint_to_datalake_definitions(
    datalake_container_name="my-company-docs",
    datalake_directory_name="from_sharepoint",
    target_folders=["Shared Documents/Projects"], # Folders to sync from SharePoint
    exclude_folders=["Shared Documents/Projects/Archive"]
)
```

## 2. Die Data-Lake-zu-Vektor-Store-Pipeline

Dies ist die Kern-RAG-Pipeline. Verwenden Sie die `default_definitions` Factory, um Dokumente aus Ihrem S3 Data Lake in
einen Vektor-Store zu verarbeiten.

- **Was es tut**: Beobachtet einen S3-Bucket, parst Dokumente, zerlegt sie in Nodes, erstellt optional Summary Nodes und
  speichert die Embeddings in Milvus. Es handhabt auch Dokumentlöschungen.
- **Schlüssel-Assets**: `observable_data_lake`, `documents`, `nodes`, `summary_nodes`, `removed_documents`.

### Anwendungsbeispiel

```python
from aihub_pipeline.util.definitions_util import default_definitions

defs = default_definitions(
    datalake_container_name="my-company-docs",
    embedding_model_name="azure/text-embedding-3-large", # Configure the embedding model
    llm_model_name="azure/gpt-4o-mini",                 # Configure the LLM for summaries
    with_summary_nodes=True                             # Enable summary node generation
)
```

## Standard-Datenabbildung

Das SDK verwendet eine konsistente Namenskonvention, um Ihre Data-Lake-Struktur auf die zugrunde liegenden
Speicher-Backends (Dokumenten-Store und Vektor-Store) abzubilden.

### Container/Bucket → Datenbank/Collection

Der Name des Top-Level S3-Buckets wird als primärer Bezeichner für Ihre Speicherressourcen verwendet und bietet eine
starke Datenisolation.

**Beispiel:**

- **Data Lake Bucket**: `s3://hr-documents/`
- **Document Store DB**: `hr-documents`
- **Vector Store Collection**: `hr-documents`

### Verzeichnis → Namespace

Innerhalb eines Buckets können Sie Verzeichnisse verwenden, um logische Trennungen zu erstellen, die auf **Namespaces**
innerhalb des Vektor-Stores abgebildet werden. Dies ermöglicht Multi-Tenancy oder logische Gruppierungen innerhalb einer
einzigen Collection.

**Beispiel:**

- **Data Lake Path**: `s3://hr-documents/onboarding/`
- **Vector Store Namespace**: `onboarding`

## Ausführen und Kombinieren von Pipelines

Um eine Pipeline auszuführen, speichern Sie Ihren Definitions-Code (z.B. `my_pipeline.py`) und verwenden Sie die Dagster
CLI.

```bash
# Start the Dagster UI and development server
dagster dev -f my_pipeline.py
```

```python
from dagster import Definitions
from aihub_pipeline.util.definitions_util import (
    default_sharepoint_to_datalake_definitions,
    default_definitions,
)

# Get definitions from both factories
sharepoint_defs = default_sharepoint_to_datalake_definitions(...)
datalake_defs = default_definitions(...)

# Combine all assets, resources, jobs, etc. into a single definition
defs = Definitions(
    assets=[*sharepoint_defs.assets, *datalake_defs.assets],
    resources={**sharepoint_defs.resources, **datalake_defs.resources},
    jobs=[*sharepoint_defs.jobs, *datalake_defs.jobs],
    schedules=[*sharepoint_defs.schedules, *datalake_defs.schedules],
    sensors=[*sharepoint_defs.sensors, *datalake_defs.sensors],
)
```
