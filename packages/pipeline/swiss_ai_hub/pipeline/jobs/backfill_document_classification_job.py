from dagster import JobDefinition, job

from swiss_ai_hub.pipeline.ops.repair.backfill_document_classification_op import (
    backfill_document_classification_op,
)


def backfill_document_classification_job(*, source_location_name: str) -> JobDefinition:
    """One-op job that classifies the documents one knowledge database ingested before classification (#2483).

    Started by the backfill sensor for a database whose classification was requested, or by hand with the
    ``aihub/bucket`` run tag, where it is a dry run unless run config says otherwise.
    """

    @job(
        name=f"{source_location_name}_backfill_document_classification",
        description="Classifies already ingested documents from their stored text. Dry run unless dry_run: false.",
    )
    def _job() -> None:
        backfill_document_classification_op()

    return _job
