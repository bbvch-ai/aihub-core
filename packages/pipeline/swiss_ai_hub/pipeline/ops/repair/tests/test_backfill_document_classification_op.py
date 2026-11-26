from datetime import datetime
from unittest.mock import patch

from dagster import build_op_context

from swiss_ai_hub.pipeline.ops.repair.backfill_document_classification_op import (
    BackfillDocumentClassificationConfig,
    backfill_document_classification_op,
)
from swiss_ai_hub.pipeline.types.backfill_work import BackfillWork
from swiss_ai_hub.pipeline.types.document_classification_backfill_report import DocumentClassificationBackfillReport
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

_MODULE = "swiss_ai_hub.pipeline.ops.repair.backfill_document_classification_op"
_REQUESTED_AT = "2026-11-17T09:30:00.123000"


def _run(config: BackfillDocumentClassificationConfig, report: DocumentClassificationBackfillReport):
    with (
        patch(f"{_MODULE}.DocumentClassificationBackfillService.backfill", return_value=report) as backfill,
        patch(f"{_MODULE}.BucketEntity.clear_classification_request") as clear,
    ):
        result = backfill_document_classification_op(build_op_context(run_tags={BUCKET_RUN_TAG: "invoices"}), config)
    return result, backfill, clear


class TestBackfillDocumentClassificationOp:
    def test_a_run_for_a_request_clears_exactly_that_request(self) -> None:
        report = DocumentClassificationBackfillReport(dry_run=False, classified=3)

        result, backfill, clear = _run(
            BackfillDocumentClassificationConfig(dry_run=False, requested_at=_REQUESTED_AT), report
        )

        backfill.assert_called_once_with(bucket="invoices", dry_run=False)
        clear.assert_called_once_with("invoices", datetime.fromisoformat(_REQUESTED_AT))
        assert result.metadata["classified"].value == 3

    def test_a_launch_by_hand_is_a_dry_run_and_clears_nothing(self) -> None:
        report = DocumentClassificationBackfillReport(dry_run=True)
        report.plan([BackfillWork.CLASSIFY, BackfillWork.CLASSIFY, BackfillWork.UP_TO_DATE])

        result, backfill, clear = _run(BackfillDocumentClassificationConfig(), report)

        backfill.assert_called_once_with(bucket="invoices", dry_run=True)
        clear.assert_not_called()
        assert result.metadata["owed_classify"].value == 2
        assert result.metadata["owed_up_to_date"].value == 1
