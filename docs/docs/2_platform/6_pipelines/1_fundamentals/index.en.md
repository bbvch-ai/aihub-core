---
title: Fundamentals
---

# Pipeline fundamentals

## Implementation with Dagster

Pipelines are defined as Python code using Dagster. This approach enables:

- Custom processing logic for specific content types, business rules, or quality standards
- Conditional workflows where processing paths vary based on document content, source, or classification
- Error handling for network issues, data anomalies, or system failures

Pipeline code is reusable across different data sources and agents. Teams can build and modify pipelines without
changing agent code.

## Data sources

The platform includes a pre-built SharePoint connector for automated synchronization with SharePoint sites and document
libraries. Documents can also be uploaded manually through the UI for processing.

Custom connectors for additional sources require implementing I/O managers and operations specific to your data source
using the [pipeline SDK](../../../3_sdk/3_building_pipelines/).

## Quality and security controls

Pipelines can include validation and security steps:

- Content validation inspects incoming data for quality and completeness. Documents failing validation can be
  quarantined for review.
- Security scanning checks for malicious content or policy violations before ingestion.
- Data sanitization applies transformation rules to redact sensitive information or enforce classification policies.

All pipeline actions are logged, creating an audit trail from document retrieval through processing to storage.
