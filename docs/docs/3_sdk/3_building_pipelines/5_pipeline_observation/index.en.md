---
title: Pipeline Observation
---

# Pipeline Observation

Effective monitoring and debugging are essential for maintaining reliable data processing pipelines. Swiss AI Hub
provides comprehensive observability tools to track pipeline execution, diagnose issues, and optimize performance.

## What you'll learn

This guide covers pipeline observation:

- **Monitoring**: Track pipeline execution and performance metrics
- **Debugging**: Diagnose and resolve pipeline failures
- **Tracing**: Understand data lineage and processing history

## Dagster UI monitoring

### Asset lineage and dependencies

The Dagster UI provides visual asset lineage tracking:

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

### Asset materialization metadata

Add rich metadata to track processing details:

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

### Partition-level monitoring

Track processing status across dynamic partitions:

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

## Next steps

- Explore `packages/pipeline/playground/` for complete observable pipeline examples
