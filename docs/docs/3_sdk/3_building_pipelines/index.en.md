---
title: Building Pipelines
---

# Building Pipelines with the Swiss AI Hub SDK

The Swiss AI Hub Pipeline SDK provides a powerful, production-ready framework for building document processing
pipelines. It's designed to ingest documents from various sources, parse them, and create searchable vector embeddings
for Retrieval-Augmented Generation (RAG) systems.

This guide explains the SDK's architecture and shows you how to configure and deploy robust, automated data pipelines.

## The Default Data Lake to Vector Store Pipeline

The SDK's core is a pre-built, configurable pipeline that handles the entire journey from raw files in a data lake to
indexed embeddings in a vector store.

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

## Key Principles

Our SDK is built on a few key principles to ensure pipelines are efficient, scalable, and maintainable:

- **Asset Factories**: Instead of writing boilerplate, you use simple factory functions to generate entire sets of
  pre-configured assets and resources (e.g., `rag_pipeline_definitions`).
- **Change-Driven Automation**: Pipelines run automatically in response to data changes, not on fixed schedules. This is
  achieved using **observable assets** that monitor source systems.
- **Document-Level Isolation**: Each document is processed in its own **partition**, meaning a failure in one document
  won't halt the entire pipeline.
- **Pluggable I/O**: Custom **I/O Managers** abstract away storage logic, making it easy to integrate with different
  databases like MongoDB and Milvus without changing your core processing code.

## Quick Start: A Complete Pipeline in Under 10 Lines

The SDK's factories make it incredibly simple to stand up a complete pipeline. The `rag_pipeline_definitions` function
bundles all the necessary assets, resources, jobs, and schedules.

Create a file named `my_pipeline.py`:

```python
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.pipeline.util import rag_pipeline_definitions

# This single function call creates a complete, production-ready pipeline that serves every
# knowledge database assigned to this ingestor, resolving the target per run.
defs = rag_pipeline_definitions(
    ingestor="my_rag",
    display_name=LocaleString(en="My RAG"),
    description=LocaleString(en="Tuned for my documents"),
    embedding_model_name="local/qwen-embedding",
    llm_model_name="local/gemma-3-multimodal-small",
    with_summary_nodes=True
)
```

To run it, simply point the Dagster UI to your file: `dagster dev -f my_pipeline.py`

This single function call provides:

- An **observable data lake** per knowledge database, detecting new or changed documents.
- A multi-stage processing workflow including **parsing**, **chunking**, and **embedding**.
- Integration with MongoDB for a **document store** and Milvus for a **vector store**.
- Pre-configured **jobs**, **schedules**, and **sensors** for production-ready automation.
- Registration as a selectable ingestor, so users can create databases for it from the admin UI with no redeploy.

## Next Steps

1. **[Pipeline Fundamentals](./1_pipeline_fundamentals/)** - Understand the architectural decisions and patterns for
   building pipelines
2. **[Core Patterns](./2_core_patterns/)** - Understand the core patterns for building pipelines with examples
3. **[Data Ingestion Pipeline](./3_data_ingestion_pipeline/)** - Configure and extend the default pipeline
4. **[Job Scheduling](./4_job_scheduling/)** - Schedule your pipelines for automatic runs
5. **[Pipeline Observation](./5_pipeline_observation/)** Monitor your pipelines for performance and errors
