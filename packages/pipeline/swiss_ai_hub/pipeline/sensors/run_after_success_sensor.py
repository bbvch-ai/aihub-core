from dagster import (
    DagsterRunStatus,
    DefaultSensorStatus,
    JobDefinition,
    RunRequest,
    RunStatusSensorContext,
    SensorDefinition,
    SkipReason,
    run_status_sensor,
)

from swiss_ai_hub.pipeline.sensors.single_flight_run_guard import SingleFlightRunGuard


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
    def _sensor(context: RunStatusSensorContext) -> RunRequest | SkipReason:
        """Skips only when the in-flight run demonstrably covers this observation.

        The triggered job snapshots the corpus when it runs, so one that started *before* this
        observation finished may not see what the observation just changed. Skipping on that would
        drop the trigger for good — a run-status sensor advances past the record either way — and
        leave deleted documents in the doc and vector stores until some later observation succeeds.
        Keying the request on the observing run keeps retries idempotent.
        """
        in_flight = SingleFlightRunGuard.in_flight_run_record(context.instance, triggered_job.name)
        observed = context.instance.get_run_record_by_id(context.dagster_run.run_id)

        covers_this_observation = (
            in_flight is not None
            and in_flight.start_time is not None
            and observed is not None
            and observed.end_time is not None
            and in_flight.start_time >= observed.end_time
        )
        if covers_this_observation:
            return SkipReason(
                f"{triggered_job.name} run {in_flight.dagster_run.run_id} started after this "
                f"observation finished, so it already covers it."
            )
        return RunRequest(run_key=context.dagster_run.run_id)

    return _sensor
