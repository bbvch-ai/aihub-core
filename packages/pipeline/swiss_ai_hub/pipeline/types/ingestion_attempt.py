from typing import Annotated, Self

from dagster import RunRecord
from pydantic import BaseModel, Field

INGESTION_RETRY_TAG = "aihub/ingestion_retry"
PIPELINE_VERSION_TAG = "aihub/pipeline_version"


class IngestionAttempt(BaseModel):
    """One run that materialized (or tried to materialize) an asset of a document's partition."""

    run_id: str
    is_retry: Annotated[bool, Field(description="Requested by the retry sensor rather than by automation or by hand.")]
    pipeline_version: Annotated[str | None, Field(description="Pipeline version a retry ran with.")] = None
    is_finished: bool
    start_time: Annotated[
        float | None,
        Field(description="Unix time the run started; its end time for a run that failed before starting."),
    ] = None
    end_time: Annotated[float | None, Field(description="Unix time the run ended; None while it has not.")] = None

    @classmethod
    def from_run_record(cls, record: RunRecord) -> Self:
        tags = record.dagster_run.tags
        return cls(
            run_id=record.dagster_run.run_id,
            is_retry=INGESTION_RETRY_TAG in tags,
            pipeline_version=tags.get(PIPELINE_VERSION_TAG),
            is_finished=record.dagster_run.is_finished,
            start_time=record.start_time or record.end_time,
            end_time=record.end_time,
        )
