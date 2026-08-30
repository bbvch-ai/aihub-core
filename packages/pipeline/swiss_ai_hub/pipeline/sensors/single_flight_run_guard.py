from typing import Annotated

from dagster import DagsterInstance, DagsterRun, RunsFilter
from dagster._core.storage.dagster_run import NOT_FINISHED_STATUSES, RunRecord


class SingleFlightRunGuard:
    """Keeps a sensor from requesting a run of a job that already has one queued or running.

    The observation and removal jobs both compare the whole corpus, so a second concurrent run
    repeats the work of the first while competing for the same global run slots.
    """

    @staticmethod
    def in_flight_run_record(
        instance: Annotated[DagsterInstance, "Instance whose run records are queried"],
        job_name: Annotated[str, "Job to check for queued or running instances"],
    ) -> RunRecord | None:
        """The record rather than the run, for callers that need its timestamps.

        Filtering by job name rather than by sensor means a manually launched run suppresses the
        sensor too, which is the behaviour an operator expects.
        """
        run_records = instance.get_run_records(
            RunsFilter(job_name=job_name, statuses=list(NOT_FINISHED_STATUSES)),
            limit=1,
        )
        return run_records[0] if run_records else None

    @staticmethod
    def in_flight_run(
        instance: Annotated[DagsterInstance, "Instance whose run records are queried"],
        job_name: Annotated[str, "Job to check for queued or running instances"],
    ) -> DagsterRun | None:
        """Returns the most recent queued or running run of the job, whatever launched it."""
        record = SingleFlightRunGuard.in_flight_run_record(instance, job_name)
        return record.dagster_run if record else None
