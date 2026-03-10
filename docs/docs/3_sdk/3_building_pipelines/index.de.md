---
title: Pipelines erstellen
source_sha: c28e1a1187f4572751f2f40995bb491c792acbc77b32d47c1d7d2704da66db16
---

# Pipelines erstellen mit dem Swiss AI Hub SDK

Das Swiss AI Hub Pipeline SDK bietet ein leistungsstarkes, produktionsreifes Framework zum Erstellen von
Dokumentenverarbeitungspipelines. Es wurde entwickelt, um Dokumente aus verschiedenen Quellen aufzunehmen, zu parsen und
durchsuchbare Vektor-Embeddings für Retrieval-Augmented Generation (RAG)-Systeme zu erstellen.

Dieser Leitfaden erklärt die Architektur des SDKs und zeigt Ihnen, wie Sie robuste, automatisierte Datenpipelines
konfigurieren und deployen.

## Die Standard-Datenlake-zu-Vektor-Store-Pipeline

Der Kern des SDKs ist eine vorgefertigte, konfigurierbare Pipeline, die den gesamten Weg von Rohdateien in einem Data
Lake bis zu indizierten Embeddings in einem Vektor-Store abdeckt.

```mermaid
graph TD
    subgraph "Source Systems"
        A["📁 SharePoint Sites"]
        B["📂 File Systems"] 
        C["📄 Wikis"]
        D["📤 Manual Uploads"]
        E["🔗 Other Sources"]
    end
    
    subgraph "Default Ingestion Pipeline"
        F("Data Lake")
        G["Document Parsing"]
        H("Document Store")
        I["Chunking & Embedding"]
        J("Vector Store")
    end
    
    subgraph "Consumption" 
        K["🤖 RAG Agents"]
    end
    
    A -->|Raw Files| F
    B -->|Raw Files| F  
    C -->|Wiki Content| F
    D -->|Uploaded Files| F
    E -->|External Data| F
    
    F -->|DataLakeFile| G
    G -->|RefDocDocument| H
    H -->|RefDocDocument| I
    I -->|TextNodes | J
    J -->|TextNodes | K  
    
    style F fill:#3a5ccc,stroke:#3451b2,color:#ffffff
    style H fill:#299764,stroke:#18794e,color:#ffffff  
    style J fill:#7e4cc9,stroke:#6f42c1,color:#ffffff
```

## Schlüsselprinzipien

Unser SDK basiert auf einigen Schlüsselprinzipien, um sicherzustellen, dass Pipelines effizient, skalierbar und wartbar
sind:

- **Asset Factories**: Anstatt Boilerplate-Code zu schreiben, verwenden Sie einfache Factory-Funktionen, um ganze Sätze
  vorkonfigurierter Assets und Ressourcen zu generieren (z.B. `default_definitions`).
- **Change-Driven Automation**: Pipelines laufen automatisch als Reaktion auf Datenänderungen, nicht nach festen
  Zeitplänen. Dies wird durch **beobachtbare Assets** erreicht, die Quellsysteme überwachen.
- **Dokumentebenen-Isolation**: Jedes Dokument wird in seiner eigenen **Partition** verarbeitet, was bedeutet, dass ein
  Fehler in einem Dokument nicht die gesamte Pipeline zum Stillstand bringt.
- **Pluggable I/O**: Benutzerdefinierte **I/O Manager** abstrahieren die Speicherlogik und erleichtern so die
  Integration mit verschiedenen Datenbanken wie MongoDB und Milvus, ohne Ihren Kernverarbeitungscode ändern zu müssen.

## Schnellstart: Eine komplette Pipeline in weniger als 10 Zeilen

Die Factories des SDKs machen es unglaublich einfach, eine komplette Pipeline aufzubauen. Die Funktion
`default_definitions` bündelt alle notwendigen Assets, Ressourcen, Jobs und Zeitpläne.

Erstellen Sie eine Datei namens `my_pipeline.py`:

```python
from aihub_pipeline.util.definitions_util import default_definitions

# This single function call creates a complete, production-ready pipeline
# that watches an S3 bucket and processes its contents into a local vector store.
defs = default_definitions(
    datalake_container_name="my-company-docs",
    embedding_model_name="local/qwen-embedding",
    llm_model_name="local/gemma-3-multimodal-small",
    with_summary_nodes=True
)
```

Um sie auszuführen, verweisen Sie einfach die Dagster UI auf Ihre Datei: `dagster dev -f my_pipeline.py`

Dieser einzige Funktionsaufruf bietet:

- Einen **beobachtbaren Data Lake**, der neue oder geänderte Dokumente automatisch erkennt.
- Einen mehrstufigen Verarbeitungs-Workflow, einschließlich **Parsing**, **Chunking** und **Embedding**.
- Integration mit MongoDB für einen **Dokumenten-Store** und Milvus für einen **Vektor-Store**.
- Vorkonfigurierte **Jobs**, **Zeitpläne** und **Sensoren** für produktionsreife Automatisierung.

## Nächste Schritte

1. **[Pipeline-Grundlagen](./1_pipeline_fundamentals/)** - Verstehen Sie die architektonischen Entscheidungen und Muster
   für den Aufbau von Pipelines
2. **[Kernmuster](./2_core_patterns/)** - Verstehen Sie die Kernmuster für den Aufbau von Pipelines mit Beispielen
3. **[Dateningestions-Pipeline](./3_data_ingestion_pipeline/)** - Konfigurieren und erweitern Sie die Standard-Pipeline
4. **[Job-Scheduling](./4_job_scheduling/)** - Planen Sie Ihre Pipelines für automatische Ausführungen
5. **[Pipeline-Beobachtung](./5_pipeline_observation/)** - Überwachen Sie Ihre Pipelines auf Leistung und Fehler
