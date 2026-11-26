from datetime import datetime

from dagster import Config, MetadataValue, OpExecutionContext, Output, op
from pydantic import Field
from swiss_ai_hub.core.persistence import BucketEntity

from swiss_ai_hub.pipeline.services.document_classification_backfill_service import (
    DocumentClassificationBackfillService,
)
from swiss_ai_hub.pipeline.types.backfill_work import BackfillWork
from swiss_ai_hub.pipeline.types.document_classification_backfill_report import DocumentClassificationBackfillReport
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag


class BackfillDocumentClassificationConfig(Config):
    """A dry run by default, so a launch without run config only reports what a real run would do.

    The backfill sensor sets `dry_run: false` and the time of the request it serves, which the run clears when it
    finishes; a launch by hand clears nothing. The request is cleared also when some documents failed: they stay owed
    and are named in the report, and the next request retries them. Keeping it would retry them on every sensor tick,
    a model call each time, for a document that may never succeed.
    """

    dry_run: bool = True
    requested_at: str | None = Field(
        default=None, description="ISO time of the request this run serves, as `BucketEntity` stores it"
    )


@op(description="Classifies the documents a database ingested before classification, from their stored text.")
def backfill_document_classification_op(
    context: OpExecutionContext, config: BackfillDocumentClassificationConfig
) -> Output[DocumentClassificationBackfillReport]:
    """Adapter around `DocumentClassificationBackfillService`; the target database comes from the `aihub/bucket` tag."""
    bucket = bucket_from_run_tag(context)
    report = DocumentClassificationBackfillService.backfill(bucket=bucket, dry_run=config.dry_run)
    if config.requested_at and not config.dry_run:
        BucketEntity.clear_classification_request(bucket, datetime.fromisoformat(config.requested_at))
    context.log.info(
        f"'{bucket}': {report.owed(BackfillWork.CLASSIFY)} to classify, {report.owed(BackfillWork.RENORMALIZE)} to "
        f"re-read; {report.classified} classified, {report.renormalized} re-read, {report.changed_meanwhile} changed "
        f"meanwhile, {len(report.failed_document_ids)} failed (dry run: {report.dry_run}, "
        f"disabled: {report.disabled}, deleting: {report.deleting})"
    )
    return Output(
        report,
        metadata={
            "dry_run": report.dry_run,
            "disabled": report.disabled,
            "deleting": report.deleting,
            **{f"owed_{work.value}": report.owed(work) for work in BackfillWork},
            "classified": report.classified,
            "renormalized": report.renormalized,
            "changed_meanwhile": report.changed_meanwhile,
            "failed": len(report.failed_document_ids),
            "failed_document_ids": MetadataValue.json(report.failed_document_ids),
        },
    )
