---
title: Job-Planung
source_sha: 02c7cd9e9caa8f896f2ad41e6c890212c6709adfb5d8713956e910c8fcdec14e
---

# Job-Planung

Sobald Ihre Pipeline definiert ist, besteht der nächste Schritt darin, ihre Ausführung zu automatisieren.

## Die hybride Automatisierungsstrategie

Anstatt die gesamte ressourcenintensive Pipeline nach einem festen Zeitplan auszuführen, trennen wir die "Überprüfung"
von der "Verarbeitung".

### 1. Zeitgesteuerte Überwachung

Ein schlanker **Job** läuft nach einem festen Zeitplan (z.B. täglich um 2 Uhr morgens). Sein einziger Zweck ist es, das
**beobachtbare Quell-Asset** (z.B. `observable_data_lake`) auszuführen. Dieser Job verarbeitet keine Dokumente; er
überprüft lediglich das Quellsystem (wie S3 oder SharePoint) auf neue oder geänderte Dateien und protokolliert deren
Versionen. Dies ist der "Puls" Ihrer Pipeline.

### 2. Änderungsgesteuerte Verarbeitung

Ein **Sensor** (`default_automation_sensor`) oder eine `AutomationCondition` auf einem Asset überwacht ständig den
Zustand Ihrer Pipeline. Wenn er feststellt, dass das beobachtbare Asset eine neue Datenversion erzeugt hat (weil der
geplante Job eine Änderung gefunden hat), löst er automatisch die nachgelagerten Verarbeitungs-Assets (wie `documents`
und `nodes`) aus.

Dieser Ansatz ist äußerst effizient, da die ressourcenintensive Dokumentenverarbeitung nur dann ausgeführt wird, wenn
tatsächlich Datenänderungen vorliegen.

## Implementierung mit SDK-Factories

Die `default_definitions`- und `default_sharepoint_to_datalake_definitions`-Factories konfigurieren diese gesamte
Automatisierungseinrichtung automatisch für Sie. Sie erstellen die notwendigen Jobs, Zeitpläne und Sensoren, um die
hybride Strategie zu implementieren.

So werden die Komponenten innerhalb eines `Definitions`-Objekts zusammengestellt:

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

Die nachgelagerten Assets selbst verwenden `AutomationCondition.eager()`, um sicherzustellen, dass sie ausgeführt
werden, sobald eine vorgelagerte Änderung vom Sensor erkannt wird.

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

- [Pipeline-Überwachung](../5_pipeline_observation/) zur Überwachung der Gesundheit und Leistung Ihrer automatisierten
  Pipelines.
