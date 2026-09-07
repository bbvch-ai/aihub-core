import logging
from typing import Annotated

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
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

logger = logging.getLogger(__name__)


def run_after_success_sensor(
    *,
    monitored_job: JobDefinition,
    triggered_job: JobDefinition,
    name: str | None = None,
    require_bucket_tag: Annotated[bool, "Propagate the observe run's bucket tag onto the triggered run"] = False,
) -> SensorDefinition:
    """Triggers ``triggered_job`` after a successful run of ``monitored_job``.

    Expresses run-level ordering between two jobs that cannot share a single asset selection —
    e.g. an observe job over an ``observable_source_asset`` and a downstream materialize job
    whose correctness depends on freshly observed partitions. Dagster forbids mixing observable
    source assets with regular assets in one ``define_asset_job`` selection, so the ordering
    must live in a sensor rather than the graph.

    With ``require_bucket_tag``, the triggered run inherits the observe run's ``aihub/bucket`` tag — the
    configurable pipeline routes each run's stores by that tag, and the coverage check below is scoped to
    the same bucket, so one database's cleanup can never be taken to cover another's.
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
        bucket = context.dagster_run.tags.get(BUCKET_RUN_TAG)
        if require_bucket_tag and not bucket:
            return SkipReason(
                f"Observe run {context.dagster_run.run_id} has no '{BUCKET_RUN_TAG}' tag; cannot route cleanup."
            )
        bucket_tag = {BUCKET_RUN_TAG: bucket} if bucket else None

        in_flight = SingleFlightRunGuard.in_flight_run_record(context.instance, triggered_job.name, bucket_tag)
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
        return RunRequest(run_key=context.dagster_run.run_id, tags=bucket_tag or {})

    return _sensor
