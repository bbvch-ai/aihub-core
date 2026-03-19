---
title: Pipeline-Beobachtung
source_sha: db8e0d8b16f92143231a326612a950e9447542b3e724a8233f71e4a323f048d8
---

# Pipeline-Beobachtung

Effektives Monitoring und Debugging sind entscheidend für die Aufrechterhaltung zuverlässiger
Datenverarbeitungspipelines. Swiss AI Hub bietet umfassende Observability-Tools, um die Pipeline-Ausführung zu
verfolgen, Probleme zu diagnostizieren und die Leistung zu optimieren.

## Was Sie lernen werden

Dieser Leitfaden behandelt die Pipeline-Beobachtung:

- **Monitoring**: Verfolgung der Pipeline-Ausführung und Leistungskennzahlen
- **Debugging**: Diagnose und Behebung von Pipeline-Fehlern
- **Tracing**: Verständnis der Datenherkunft und des Verarbeitungsverlaufs

## Dagster UI-Monitoring

### Asset-Herkunft und Abhängigkeiten

Die Dagster UI bietet eine visuelle Verfolgung der Asset-Herkunft:

```python
# View asset dependencies and execution status
@graph_asset(
    key=AssetKey(["documents"]),
    ins={"data_lake_file": AssetIn(key=AssetKey(["data_lake"]))},
    description="Process data lake files into RefDocs",
)
def documents(data_lake_file: DataLakeFile) -> RefDocDocument:
    """Asset with clear lineage tracking."""
    return process_document(data_lake_file)
```

### Asset-Materialisierungs-Metadaten

Fügen Sie umfangreiche Metadaten hinzu, um Verarbeitungsdetails zu verfolgen:

```python
@op
def parse_document_with_metadata(
    context: OpExecutionContext, 
    data_lake_file: DataLakeFile
) -> RefDocDocument:
    """Operation with comprehensive metadata logging."""
    start_time = time.time()
    
    # Process document
    document = parse_document(data_lake_file)
    
    processing_time = time.time() - start_time
    
    # Add detailed metadata
    context.add_output_metadata(
        metadata={
            "file_size_mb": data_lake_file.size / 1e6,
            "processing_time_seconds": processing_time,
            "document_pages": len(document.pages) if hasattr(document, 'pages') else 1,
            "text_length": len(document.text),
            "parser_version": "mineru-2.7",
            "success_rate": 1.0,
            "Table": MetadataValue.table(
                records=[{
                    "metric": "file_size_mb",
                    "value": data_lake_file.size / 1e6
                }, {
                    "metric": "processing_time",
                    "value": f"{processing_time:.2f}s"
                }]
            )
        }
    )
    
    context.log.info(f"Processed document: {data_lake_file.name} in {processing_time:.2f}s")
    return document
```

### Monitoring auf Partitionsebene

Verfolgen Sie den Verarbeitungsstatus über dynamische Partitionen hinweg:

```python
@asset(
    partitions_def=document_partitions,
    automation_condition=AutomationCondition.eager(),
)
def partitioned_processing(context: AssetExecutionContext) -> ProcessingResult:
    """Monitor partition-level execution."""
    partition_key = context.partition_key
    
    context.log.info(f"Processing partition: {partition_key}")
    
    # Add partition-specific metadata
    context.add_output_metadata(
        metadata={
            "partition_key": partition_key,
            "partition_timestamp": context.partition_time_window.start.isoformat(),
            "processing_node": os.getenv("HOSTNAME", "unknown"),
        }
    )
    
    return process_partition_data(partition_key)
```

## Nächste Schritte

- Erkunden Sie `packages/pipeline/playground/` für vollständige Beispiele beobachtbarer Pipelines
