---
title: Pipeline-Beobachtung
index: 5
source_sha: "eee9dfa88a03f799fce02173e3ce3e1955669c6832397213f80416b98a712a2f"
---

# Pipeline-Beobachtung

Effektives Monitoring und Debugging sind unerlässlich für die Aufrechterhaltung zuverlässiger Datenverarbeitungspipelines. AI-Hub bietet umfassende Observability-Tools, um die Pipeline-Ausführung zu verfolgen, Probleme zu diagnostizieren und die Leistung zu optimieren.

## Was Sie lernen werden

Dieser Leitfaden behandelt die Pipeline-Beobachtung:

- **Monitoring**: Verfolgen Sie die Pipeline-Ausführung und Leistungsmetriken
- **Debugging**: Diagnostizieren und beheben Sie Pipeline-Fehler
- **Tracing**: Verstehen Sie die Datenherkunft und den Verarbeitungsverlauf

## Dagster UI-Monitoring

### Asset-Abstammung und -Abhängigkeiten

Die Dagster UI bietet eine visuelle Verfolgung der Asset-Abstammung:

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

### Metadaten zur Asset-Materialisierung

Fügen Sie reichhaltige Metadaten hinzu, um Verarbeitungsdetails zu verfolgen:

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
            "parser_version": "docling-1.0",
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

## Was Sie gelernt haben

- **Umfassendes Monitoring**: Nutzen Sie die Dagster UI und benutzerdefinierte Metriken für vollständige Observability

## Nächste Schritte

- Erkunden Sie `aihub_pipeline/playground/` für vollständige Beispiele beobachtbarer Pipelines
