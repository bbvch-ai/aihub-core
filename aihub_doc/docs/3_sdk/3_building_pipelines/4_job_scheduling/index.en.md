---
title: ' Job Scheduling'
---

# Job Scheduling

Once your pipeline is defined, the next step is to automate its execution.

## The Hybrid Automation Strategy

Instead of running the entire heavy pipeline on a fixed schedule, we separate the "checking" from the "processing."

### 1. Scheduled Observation

A lightweight **job** runs on a fixed schedule (e.g., daily at 2 AM). Its only purpose is to execute the **observable
source asset** (e.g., `observable_data_lake`). This job doesn't process any documents; it simply checks the source
system (like S3 or SharePoint) for new or modified files and records their versions. This is the "pulse" of your
pipeline.

### 2. Change-Driven Processing

A **sensor** (`default_automation_sensor`) or an `AutomationCondition` on an asset constantly monitors the state of your
pipeline. When it detects that the observable asset has produced a new data version (because the scheduled job found a
change), it automatically triggers the downstream processing assets (like `documents` and `nodes`).

This approach is highly efficient because the resource-intensive document processing work only runs when there are
actual data changes.

## Implementation with SDK Factories

The `default_definitions` and `default_sharepoint_to_datalake_definitions` factories automatically configure this entire
automation setup for you. They create the necessary jobs, schedules, and sensors to implement the hybrid strategy.

Here is how the components are assembled within a `Definitions` object:

```python
# This pattern is automatically configured by the SDK's default factories.
from aihub_pipeline.jobs.factory import observe_source_job
from aihub_pipeline.schedules.factory import daily_schedule_at
from aihub_pipeline.sensors.factory import default_automation_sensor

# A. A job is created specifically to run the observation asset.
# This is a lightweight, fast-running job.
observe_job = observe_source_job(
    observable_asset=observable_data_lake,
    source_location_name="my_company_docs",
)

# B. A schedule is attached to the observation job.
# This tells Dagster to run the check at a specific time.
observe_schedule = daily_schedule_at(
    job=observe_job,
    hour=2, # Run at 2 AM daily
    minute=0,
)

# C. A sensor is created to trigger the actual processing.
# It watches for new versions created by the observe_job.
automation_sensor = default_automation_sensor(all_pipeline_assets)

# The factory bundles these into the final Definitions object.
defs = Definitions(
    assets=all_pipeline_assets,
    jobs=[observe_job],
    schedules=[observe_schedule],
    sensors=[automation_sensor],
    # ...resources and executors
)
```

The downstream assets themselves use `AutomationCondition.eager()` to ensure they run as soon as an upstream change is
detected by the sensor.

```python
@graph_asset(
    key=AssetKey(["production", "documents"]),
    ins={"data_lake_file": AssetIn(key=AssetKey(["production", "data_lake"]))},
    # This asset will run automatically when the sensor detects a change
    # in the upstream 'data_lake' asset for a given partition.
    automation_condition=AutomationCondition.eager(),
)
def production_documents(data_lake_file: DataLakeFile) -> RefDocDocument:
    return process_document(data_lake_file)
```

## Next Steps

- [Pipeline Observation](../5_pipeline_observation/) for monitoring the health and performance of your automated
  pipelines.
