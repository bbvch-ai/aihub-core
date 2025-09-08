---
title: "Scheduling"
index: 4
---
# Scheduling


## Scheduling strategy

### Observable-driven processing

The preferred approach uses observable assets with automation conditions to process data reactively:

```python
# Primary strategy: React to data changes
@observable_source_asset(
    key=AssetKey(["production", "data_lake"]),
    partitions_def=document_partitions,
)
def production_data_observer(context: OpExecutionContext) -> DataVersions:
    """Monitor production data lake for document changes."""
    return scan_for_changed_documents(context)

# Downstream assets process automatically
@graph_asset(
    key=AssetKey(["production", "documents"]),
    ins={"data_lake_file": AssetIn(key=AssetKey(["production", "data_lake"]))},
    automation_condition=AutomationCondition.eager(),
)
def production_documents(data_lake_file: DataLakeFile) -> RefDocDocument:
    return process_document(data_lake_file)
```

### Scheduled processing

For scenarios requiring time-based processing, use Dagster's scheduling capabilities:

```python
from aihub_pipeline.schedules.factory import daily_schedule_at
from aihub_pipeline.jobs.factory import observe_source_job

# Daily batch processing
daily_batch = daily_schedule_at(
    job=observe_source_job(observable_asset, "production"),
    hour=2,  # Run at 2 AM
    minute=0,
)


```
This observes an asset every night at 2 AM.


## Resource configuration for production

### Environment-specific resources

Configure different resource settings for production environments:

```python
def production_resources() -> dict[str, ConfigurableResource]:
    return {
        # High-performance document parsing
        "document_parser": DocumentParserResource(
            loader_type=LoaderType.BOTH,
            timeout=300,  # Longer timeout for complex documents
            max_retries=3,
        ),
        
        # Production vector store
        **mongo_aisearch_storage_context_resources(
            store_name="production_knowledge",
            namespace_name="main",
            connection_pool_size=20,
        ),
        
        # Production data lake
        **azure_data_lake_resources(
            account_name=os.getenv("AZURE_STORAGE_ACCOUNT"),
            container_name="production-documents",
            directory_name="processed",
            connection_timeout=60,
        ),
        
        # High-capacity embedding model
        "embedding_model": EmbeddingModelResource(
            embedding_config=EmbeddingModelConfig(
                model_name="azure/text-embedding-3-large",
                batch_size=100,
                max_concurrent_requests=10,
            )
        ),
        
        # Production language model
        "language_model": LanguageModelResource(
            llm_config=LLMConfig(
                model_name="azure/gpt-4o",
                max_tokens=4000,
                temperature=0.1,
                request_timeout=120,
            )
        ),
    }
```


## Job definitions and organization

### Structured job organization

Organize jobs by functionality and operational requirements:

```python
# Source observation jobs
observe_sharepoint_job = observe_source_job(
    observable_asset=sharepoint_observer,
    namespace_name="production",
    job_name="observe_sharepoint",
)

observe_filesystem_job = observe_source_job(
    observable_asset=filesystem_observer,
    namespace_name="production", 
    job_name="observe_filesystem",
)

```


## Next steps

With production scheduling mastered, complete your pipeline expertise with:
- [Pipeline observation](../5_pipeline_observation/) for monitoring and debugging production systems