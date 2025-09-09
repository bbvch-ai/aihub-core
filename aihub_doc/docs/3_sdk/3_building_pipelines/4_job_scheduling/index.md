---
title: " Job Scheduling"
index: 4
---
# Job Scheduling


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

- [Pipeline observation](../5_pipeline_observation/) for monitoring and debugging production systems