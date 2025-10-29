---
title: ' Job-Planung'
source_sha: "d628dbfa502f3674ca4d7f75ab0cfc175982529419bd323a831f4bf8117b5eb8"
---

# Job-Planung

Sobald Ihre Pipeline definiert ist, besteht der nächste Schritt darin, ihre Ausführung zu automatisieren.

## Die hybride Automatisierungsstrategie

Anstatt die gesamte ressourcenintensive Pipeline nach einem festen Zeitplan auszuführen, trennen wir das „Prüfen“ vom „Verarbeiten“.

### 1. Geplante Überwachung

Ein schlanker **Job** wird nach einem festen Zeitplan ausgeführt (z.B. täglich um 2 Uhr morgens). Sein einziger Zweck ist es, das **beobachtbare Quell-Asset** (z.B. `observable_data_lake`) auszuführen. Dieser Job verarbeitet keine Dokumente; er prüft lediglich das Quellsystem (wie S3 oder SharePoint) auf neue oder geänderte Dateien und erfasst deren Versionen. Dies ist der „Puls“ Ihrer Pipeline.

### 2. Änderungsgesteuerte Verarbeitung

Ein **Sensor** (`default_automation_sensor`) oder eine `AutomationCondition` auf einem Asset überwacht ständig den Zustand Ihrer Pipeline. Wenn er erkennt, dass das beobachtbare Asset eine neue Datenversion produziert hat (weil der geplante Job eine Änderung gefunden hat), löst er automatisch die nachgelagerten Verarbeitungs-Assets (wie `documents` und `nodes`) aus.

Dieser Ansatz ist hocheffizient, da die ressourcenintensive Dokumentenverarbeitung nur dann ausgeführt wird, wenn tatsächliche Datenänderungen vorliegen.

## Implementierung mit SDK-Factories

Die Factories `default_definitions` und `default_sharepoint_to_datalake_definitions` konfigurieren dieses gesamte Automatisierungs-Setup automatisch für Sie. Sie erstellen die notwendigen Jobs, Zeitpläne und Sensoren, um die hybride Strategie zu implementieren.

Hier wird gezeigt, wie die Komponenten innerhalb eines `Definitions`-Objekts zusammengebaut werden:

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

Die nachgelagerten Assets selbst verwenden `AutomationCondition.eager()`, um sicherzustellen, dass sie ausgeführt werden, sobald eine vorgelagerte Änderung vom Sensor erkannt wird.

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

## Nächste Schritte

  - [Pipeline-Überwachung](../5_pipeline_observation/) zur Überwachung der Integrität und Leistung Ihrer automatisierten Pipelines.
