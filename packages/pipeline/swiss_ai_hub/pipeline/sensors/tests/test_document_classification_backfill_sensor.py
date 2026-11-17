"""The backfill sensor turns a database's classification request into one run at a time (#2483)."""

from collections.abc import Iterator
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from dagster import DagsterInstance, build_sensor_context

from swiss_ai_hub.pipeline.jobs.backfill_document_classification_job import backfill_document_classification_job
from swiss_ai_hub.pipeline.sensors.document_classification_backfill_sensor import (
    BACKFILL_REQUEST_TAG,
    BACKFILL_TARGET_TAG,
    MAX_ATTEMPTS_PER_REQUEST,
    document_classification_backfill_sensor,
)
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

_MODULE = "swiss_ai_hub.pipeline.sensors.document_classification_backfill_sensor"
_REQUESTED_AT = datetime(2026, 11, 17, 9, 30, 0, 123000)
_JOB = backfill_document_classification_job(source_location_name="document_ingestion")


@pytest.fixture
def instance() -> Iterator[DagsterInstance]:
    with DagsterInstance.ephemeral() as ephemeral:
        yield ephemeral


def _bucket(name: str, ingestor: str = "document_ingestion") -> MagicMock:
    return MagicMock(bucket_name=name, ingestor=ingestor, classification_requested_at=_REQUESTED_AT)


def _tick(instance: DagsterInstance, *buckets: MagicMock):
    sensor = document_classification_backfill_sensor(_JOB, ingestor="document_ingestion")
    with (
        patch(f"{_MODULE}.ensure_main_db_connection"),
        patch(f"{_MODULE}.BucketEntity.get_classification_requested_buckets", return_value=list(buckets)),
    ):
        return sensor.evaluate_tick(build_sensor_context(instance=instance))


def test_a_requested_database_gets_a_real_run_that_knows_which_request_it_serves(instance) -> None:
    result = _tick(instance, _bucket("invoices"))

    [request] = result.run_requests
    assert request.tags[BUCKET_RUN_TAG] == "invoices"
    assert request.tags[BACKFILL_TARGET_TAG] == "invoices"
    assert request.tags[BACKFILL_REQUEST_TAG] == _REQUESTED_AT.isoformat()
    op_config = request.run_config["ops"]["backfill_document_classification_op"]["config"]
    assert op_config == {"dry_run": False, "requested_at": _REQUESTED_AT.isoformat()}
    assert request.run_key == f"classification_backfill_invoices_{_REQUESTED_AT.isoformat()}_0"


def test_another_pipelines_databases_are_left_to_it(instance) -> None:
    result = _tick(instance, _bucket("contracts", ingestor="acme_ocr"))

    assert not result.run_requests
    assert "0 backfill(s) requested" in str(result.skip_message)


def test_no_second_run_while_one_is_running(instance) -> None:
    with patch.object(instance, "get_run_records", return_value=[MagicMock()]):
        result = _tick(instance, _bucket("invoices"))

    assert not result.run_requests
    assert "1 backfill(s) requested, none ready" in str(result.skip_message)


def test_a_failed_run_is_driven_again_under_a_new_key(instance) -> None:
    with patch.object(instance, "get_runs_count", return_value=1):
        result = _tick(instance, _bucket("invoices"))

    [request] = result.run_requests
    assert request.run_key.endswith("_1")


def test_a_request_whose_runs_keep_failing_is_given_up_and_kept_as_failed(instance) -> None:
    with (
        patch.object(instance, "get_runs_count", return_value=MAX_ATTEMPTS_PER_REQUEST),
        patch(f"{_MODULE}.BucketEntity.fail_classification_request") as fail,
    ):
        result = _tick(instance, _bucket("invoices"))

    assert not result.run_requests
    fail.assert_called_once_with("invoices", _REQUESTED_AT)


def test_attempts_are_counted_per_request_so_a_new_request_starts_over(instance) -> None:
    with patch.object(instance, "get_runs_count", return_value=0) as count:
        _tick(instance, _bucket("invoices"))

    counted_tags = count.call_args.args[0].tags
    assert counted_tags == {BACKFILL_TARGET_TAG: "invoices", BACKFILL_REQUEST_TAG: _REQUESTED_AT.isoformat()}
