from dagster import (
    DagsterRunStatus,
    DefaultSensorStatus,
    JobDefinition,
    RunRequest,
    SensorDefinition,
    run_status_sensor,
)


def run_after_success_sensor(
    *,
    monitored_job: JobDefinition,
    triggered_job: JobDefinition,
    name: str | None = None,
) -> SensorDefinition:
    """Triggers ``triggered_job`` after a successful run of ``monitored_job``.

    Expresses run-level ordering between two jobs that cannot share a single asset selection —
    e.g. an observe job over an ``observable_source_asset`` and a downstream materialize job
    whose correctness depends on freshly observed partitions. Dagster forbids mixing observable
    source assets with regular assets in one ``define_asset_job`` selection, so the ordering
    must live in a sensor rather than the graph.
    """
    sensor_name = name or f"trigger_{triggered_job.name}_after_{monitored_job.name}"

    @run_status_sensor(
        name=sensor_name,
        run_status=DagsterRunStatus.SUCCESS,
        monitored_jobs=[monitored_job],
        request_job=triggered_job,
        default_status=DefaultSensorStatus.RUNNING,
    )
    def _sensor(_context) -> RunRequest:
        return RunRequest()

    return _sensor
