from typing import Annotated

from dagster import DagsterInstance, RunsFilter

from swiss_ai_hub.pipeline.util.partition_utils import PARTITIONS_TRUNCATED_TAG

_RUN_KEY_TAG = "dagster/run_key"


class ObservationRunHistory:
    """Reads facts about past observation runs that the sensor cannot hold in its own cursor.

    A run executes in a different process from the sensor and cannot write the sensor's cursor, so
    anything it needs to report travels back as a run tag.
    """

    @staticmethod
    def run_exists_for_run_key(
        instance: Annotated[DagsterInstance, "Instance whose run records are queried"],
        job_name: Annotated[str, "Job the run key belongs to"],
        run_key: Annotated[str, "Run key a previous tick requested"],
    ) -> bool:
        """Whether a requested run key ever became a run.

        The daemon creates the run only after the sensor body returns, so a crash in that window
        loses the request silently; the next tick uses this to notice and ask again.
        """
        return bool(
            instance.get_run_records(
                RunsFilter(job_name=job_name, tags={_RUN_KEY_TAG: run_key}),
                limit=1,
            )
        )

    @staticmethod
    def requested_run_missing(
        instance: Annotated[DagsterInstance, "Instance whose run records are queried"],
        job_name: Annotated[str, "Job the run key belongs to"],
        run_key: Annotated[str | None, "Run key the previous tick requested, if it requested one"],
    ) -> bool:
        """Whether a run key was requested but never became a run, so the tick should ask again."""
        if not run_key:
            return False
        return not ObservationRunHistory.run_exists_for_run_key(instance, job_name, run_key)

    @staticmethod
    def latest_truncating_run_id(
        instance: Annotated[DagsterInstance, "Instance whose run records are queried"],
        job_name: Annotated[str, "Observation job to inspect"],
    ) -> str | None:
        """Run id of the most recent observation that hit the ``max_partitions`` cap.

        Such a run only partitioned part of the corpus, so the sensor has to observe again rather
        than wait for the nightly schedule.
        """
        run_records = instance.get_run_records(
            RunsFilter(job_name=job_name, tags=PARTITIONS_TRUNCATED_TAG),
            limit=1,
        )
        return run_records[0].dagster_run.run_id if run_records else None
