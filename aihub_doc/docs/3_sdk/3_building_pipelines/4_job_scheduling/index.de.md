---
title: Auftragsplanung
index: 4
source_sha: "6407d761533898a9b484a9942a106345bc5b1f961d889251cea7fda4b644b677"
---

# Auftragsplanung

## Planungsstrategie

### Observable-gesteuerte Verarbeitung

Der bevorzugte Ansatz verwendet beobachtbare Assets mit Automatisierungsbedingungen, um Daten reaktiv zu verarbeiten:

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

### Zeitgesteuerte Verarbeitung

Für Szenarien, die eine zeitbasierte Verarbeitung erfordern, nutzen Sie Dagsters Planungsfunktionen:

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

Dies beobachtet ein Asset jede Nacht um 2 Uhr morgens.

## Job-Definitionen und -Organisation

### Strukturierte Job-Organisation

Organisieren Sie Jobs nach Funktionalität und betrieblichen Anforderungen:

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

## Nächste Schritte

- [Pipeline-Beobachtung](../5_pipeline_observation/) zur Überwachung und Fehlerbehebung in Produktionssystemen
