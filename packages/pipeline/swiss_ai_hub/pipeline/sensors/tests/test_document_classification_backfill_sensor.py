"""The backfill sensor turns a database's classification request into one run at a time (#2483)."""

from collections.abc import Iterator
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from dagster import DagsterInstance, build_sensor_context

from swiss_ai_hub.pipeline.jobs.backfill_document_classification_job import backfill_document_classification_job
from swiss_ai_hub.pipeline.sensors.document_classification_backfill_sensor import (
    BACKFILL_TARGET_TAG,
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
