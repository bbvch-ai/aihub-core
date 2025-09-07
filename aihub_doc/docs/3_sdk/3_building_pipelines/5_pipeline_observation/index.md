---
title: "Pipeline Observation"
index: 5
---

# Pipeline Observation

Effective monitoring and debugging are essential for maintaining reliable data processing pipelines. AI-Hub provides comprehensive observability tools to track pipeline execution, diagnose issues, and optimize performance.

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

## Error handling and debugging

### Structured error logging

Implement comprehensive error handling with context:

```python
from aihub_pipeline.types.ProcessingError import ProcessingError

@op
def robust_document_processing(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
    document_parser: DocumentParserResource,
) -> RefDocDocument:
    """Operation with structured error handling."""
    try:
        context.log.info(f"Processing file: {data_lake_file.name}")
        
        # Attempt document processing
        document = document_parser.parse_file(data_lake_file.uri)
        
        # Validate result
        if not document or not document.text.strip():
            raise ProcessingError(
                error_type="empty_document",
                file_uri=data_lake_file.uri,
                details="Document parsing resulted in empty content"
            )
        
        context.log.info(f"Successfully processed: {data_lake_file.name}")
        return document
        
    except ProcessingError as e:
        # Log structured error with context
        context.log.error(
            f"Processing error: {e.error_type}",
            extra={
                "file_uri": data_lake_file.uri,
                "file_size": data_lake_file.size,
                "error_details": e.details,
                "retry_count": context.retry_number,
            }
        )
        
        # Add error metadata for monitoring
        context.add_output_metadata(
            metadata={
                "error_type": e.error_type,
                "error_details": e.details,
                "processing_status": "failed",
            }
        )
        raise
        
    except Exception as e:
        # Handle unexpected errors
        context.log.error(
            f"Unexpected error processing {data_lake_file.name}: {str(e)}",
            extra={
                "file_uri": data_lake_file.uri,
                "exception_type": type(e).__name__,
                "stack_trace": traceback.format_exc(),
            }
        )
        raise
```


## What you learned

- **Comprehensive monitoring**: Use Dagster UI and custom metrics for full observability
- **Error handling**: Implement structured error logging with context

## Next steps

- Explore `aihub_pipeline/playground/__init__.py` for complete observable pipeline examples