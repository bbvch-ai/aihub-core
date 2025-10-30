---
title: Fundamentals
index: 1
---

# Pipeline fundamentals

Data pipelines synchronize information between source systems and knowledge bases. They monitor SharePoint sites, detect
changes (additions, modifications, deletions), and process those changes to maintain current knowledge bases. Users can
also upload documents manually to the data lake for processing.

Pipelines convert documents into vector databases where text is parsed, chunked, and embedded. This structure enables
semantic search based on meaning rather than keyword matching.

## Implementation with Dagster

Pipelines are built on Dagster and defined as Python code. This enables:

- Custom processing logic for specific content types, business rules, or quality standards
- Conditional workflows where processing paths vary based on document content, source, or classification
- Error handling for network issues, data anomalies, or system failures

Pipeline code is reusable across different data sources and agents.

## Document lifecycle management

Pipelines handle the full document lifecycle:

When a document is added, the pipeline processes it and stores embeddings in the knowledge base.

When a document is modified, the pipeline removes embeddings from the old version before processing and storing the new
version.

When a document is deleted, the pipeline removes all associated embeddings from the knowledge base.

This prevents agents from retrieving information from outdated or deleted documents.

## Data sources

The platform includes a pre-built SharePoint connector for automated synchronization with SharePoint sites and document
libraries.

For other data sources, you can manually upload documents to the data lake via the UI. The pipeline processes uploaded
files through the same parsing, chunking, and embedding stages as SharePoint documents.

Custom connectors for additional sources can be implemented using the
[pipeline SDK](../../../3_sdk/3_building_pipelines/). This requires developing I/O managers and operations specific to
your data source.

## Quality and security controls

Pipelines can include validation and security steps:

Content validation inspects incoming data for quality and completeness. Documents failing validation can be quarantined
for review.

Security scanning checks for malicious content or policy violations before ingestion.

Data sanitization applies transformation rules to redact sensitive information or enforce classification policies.

All pipeline actions are logged, creating an audit trail from initial retrieval through processing to storage.
