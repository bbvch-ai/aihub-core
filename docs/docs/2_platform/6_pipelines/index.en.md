---
title: Data pipelines
---

# Data pipelines

Pipelines are automated workflows that transform documents into searchable knowledge bases for AI agents. They monitor
file storage locations, process documents when changes occur, and maintain vector databases that agents query for
information.

## Document processing workflow

Raw documents cannot be directly queried by agents. PDFs and Word files must be converted to text, split into manageable
chunks, and transformed into vector embeddings that enable semantic search. Pipelines handle this transformation
automatically.

```mermaid
flowchart LR
    A[📄 Documents<br/>SharePoint/Upload] --> B[📖 Parse<br/>Extract text & structure]
    B --> C[✂️ Chunk<br/>Break into pieces]
    C --> D[🔢 Embed<br/>Convert to vectors]
    D --> E[💾 Store<br/>Vector database]
    E --> F[🤖 Agents<br/>Query & retrieve]

    style A fill:#1e40af,stroke:#1e3a8a,stroke-width:2px,color:#fff
    style B fill:#b45309,stroke:#92400e,stroke-width:2px,color:#fff
    style C fill:#9f1239,stroke:#881337,stroke-width:2px,color:#fff
    style D fill:#047857,stroke:#065f46,stroke-width:2px,color:#fff
    style E fill:#6d28d9,stroke:#5b21b6,stroke-width:2px,color:#fff
    style F fill:#b91c1c,stroke:#991b1b,stroke-width:2px,color:#fff
```

The diagram shows the complete flow from document ingestion through to agent queries. Each stage transforms the data to
make it searchable and retrievable.

## Automatic synchronization

Pipelines monitor data sources for changes. When a document is added, modified, or deleted, the pipeline processes the
change and updates the knowledge base. This keeps agent responses current without manual intervention.

## Orchestration with Dagster

Dagster orchestrates pipeline execution, handling scheduling, retries, and logging. Each processing step is tracked,
creating an audit trail from document ingestion through to storage. You can review pipeline runs to troubleshoot issues,
verify document processing, and monitor data quality.
