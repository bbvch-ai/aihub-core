"""The retry sensor re-drives a failed document's earliest failed asset and reports the failure on its record."""

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from dagster import (
    AssetKey,
    AssetsDefinition,
    DagsterInstance,
    DagsterRun,
    DagsterRunStatus,
    Definitions,
    DynamicPartitionsDefinition,
    asset,
    build_sensor_context,
    partition_loading_context,
)
from dagster._core.storage.partition_status_cache import AssetPartitionStatus
from dagster._core.storage.tags import PARTITION_NAME_TAG, PRIORITY_TAG

from swiss_ai_hub.pipeline.jobs.retry_failed_ingestion_job import retry_failed_ingestion_job
from swiss_ai_hub.pipeline.sensors.failed_ingestion_retry_sensor import (
    INGESTION_RETRY_ORIGIN_TAG,
    RETRY_RUN_PRIORITY,
    _clear_failures_of_fresh_runs,
    _report_on_record,
    failed_ingestion_retry_sensor,
)
from swiss_ai_hub.pipeline.types.ingestion_attempt import INGESTION_RETRY_TAG, PIPELINE_VERSION_TAG
from swiss_ai_hub.pipeline.types.ingestion_retry_action import IngestionRetryAction
from swiss_ai_hub.pipeline.types.ingestion_retry_decision import IngestionRetryDecision
from swiss_ai_hub.pipeline.util.id_utils import uri_to_id
from swiss_ai_hub.pipeline.util.partition_utils import make_composite_partition_key
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

_MODULE = "swiss_ai_hub.pipeline.sensors.failed_ingestion_retry_sensor"
_VERSION = "0.327.0"
_PARTITIONS = DynamicPartitionsDefinition(name="document_ingestion_document_partitions")
_DOCUMENTS = AssetKey(["document_ingestion_datalake_to_vectorstore", "documents"])
_NODES = AssetKey(["document_ingestion_datalake_to_vectorstore", "nodes"])
_SUMMARIES = AssetKey(["document_ingestion_datalake_to_vectorstore", "summary_nodes"])
_ASSETS = [_DOCUMENTS, _NODES, _SUMMARIES]
_JOB = retry_failed_ingestion_job(source_location_name="document_ingestion", asset_keys=_ASSETS)
_INVOICE = make_composite_partition_key("invoices", "s3://invoices/finance/q3.pdf")
_CONTRACT = make_composite_partition_key("contracts", "s3://contracts/legal/nda.pdf")


@pytest.fixture
def instance() -> Iterator[DagsterInstance]:
    with DagsterInstance.ephemeral() as ephemeral:
        ephemeral.add_dynamic_partitions(_PARTITIONS.name, [_INVOICE, _CONTRACT])
        yield ephemeral


def _bucket(name: str, ingestor: str = "document_ingestion", deleting: bool = False) -> MagicMock:
    return MagicMock(bucket_name=name, ingestor=ingestor, deleting=deleting)


def _failed_run(instance: DagsterInstance, run_id: str, partition_key: str, **tags: str) -> None:
    instance.add_run(
        DagsterRun(
            job_name="__ASSET_JOB",
            run_id=run_id,
            tags={PARTITION_NAME_TAG: partition_key, **tags},
            status=DagsterRunStatus.FAILURE,
        )
    )


def _stand_in(key: AssetKey, upstream: AssetKey | None) -> AssetsDefinition:
    @asset(key=key, partitions_def=_PARTITIONS, deps=[upstream] if upstream else [])
    def _asset() -> None:
        return None

    return _asset


_SENSOR = failed_ingestion_retry_sensor(
    _JOB,
    ingestor="document_ingestion",
    asset_keys=_ASSETS,
    partitions=_PARTITIONS,
    max_retries=3,
    backoff_minutes=10,
    pipeline_version=_VERSION,
)
_REPOSITORY = Definitions(
    assets=[_stand_in(_DOCUMENTS, None), _stand_in(_NODES, _DOCUMENTS), _stand_in(_SUMMARIES, _NODES)],
    jobs=[_JOB],
    sensors=[_SENSOR],
).get_repository_def()


def _tick(instance: DagsterInstance, statuses: dict[AssetKey, dict], buckets: list[MagicMock] | None = None):
    with (
        patch(f"{_MODULE}.ensure_main_db_connection"),
        patch(f"{_MODULE}.BucketEntity.get_all_buckets", return_value=buckets or [_bucket("invoices")]),
        patch.object(instance, "get_status_by_partition", side_effect=lambda key, *_: statuses.get(key, {})),
        patch(f"{_MODULE}._report_on_record") as report,
        # The daemon threads its instance into the run requests' partition check; a test tick does not.
        partition_loading_context(dynamic_partitions_store=instance),
    ):
        context = build_sensor_context(instance=instance, repository_def=_REPOSITORY)
        return _SENSOR.evaluate_tick(context), report


def test_a_failed_document_is_retried_without_its_file_changing(instance) -> None:
    _failed_run(instance, "eager-run", _INVOICE)

    result, report = _tick(instance, {_DOCUMENTS: {_INVOICE: AssetPartitionStatus.FAILED}})

    [request] = result.run_requests
    assert request.partition_key == _INVOICE
    assert request.asset_selection == [_DOCUMENTS]
    assert request.tags[INGESTION_RETRY_TAG] == "true"
    assert request.tags[INGESTION_RETRY_ORIGIN_TAG] == "eager-run"
    assert request.tags[PIPELINE_VERSION_TAG] == _VERSION
    assert request.tags[BUCKET_RUN_TAG] == "invoices"
    assert request.tags[PRIORITY_TAG] == RETRY_RUN_PRIORITY
    assert request.run_key == f"ingestion_retry_documents_{_INVOICE}_eager-run_{_VERSION}_1"
    report.assert_called_once()


def test_only_the_earliest_failed_asset_is_retried_and_automation_carries_the_rest(instance) -> None:
    _failed_run(instance, "eager-run", _INVOICE)

    result, _ = _tick(
        instance,
        {
            _DOCUMENTS: {_INVOICE: AssetPartitionStatus.MATERIALIZED},
            _NODES: {_INVOICE: AssetPartitionStatus.FAILED},
            _SUMMARIES: {_INVOICE: AssetPartitionStatus.FAILED},
        },
    )

    [request] = result.run_requests
    assert request.asset_selection == [_NODES]


def test_a_partition_still_ingesting_is_left_alone(instance) -> None:
    _failed_run(instance, "eager-run", _INVOICE)

    result, report = _tick(
        instance,
        {_DOCUMENTS: {_INVOICE: AssetPartitionStatus.IN_PROGRESS}, _NODES: {_INVOICE: AssetPartitionStatus.FAILED}},
    )

    assert not result.run_requests
    report.assert_not_called()


def test_a_document_that_used_its_retries_is_reported_given_up_and_not_run_again(instance) -> None:
    _failed_run(instance, "eager-run", _INVOICE)
    for number in (1, 2, 3):
        _failed_run(
            instance, f"retry-{number}", _INVOICE, **{INGESTION_RETRY_TAG: "true", PIPELINE_VERSION_TAG: _VERSION}
        )

    result, report = _tick(instance, {_DOCUMENTS: {_INVOICE: AssetPartitionStatus.FAILED}})

    assert not result.run_requests
    [call] = report.call_args_list
    assert call.args[1].failed_attempts == 4


def test_databases_of_another_pipeline_or_being_deleted_are_left_to_others(instance) -> None:
    _failed_run(instance, "eager-invoice", _INVOICE)
    _failed_run(instance, "eager-contract", _CONTRACT)

    result, report = _tick(
        instance,
        {_DOCUMENTS: {_INVOICE: AssetPartitionStatus.FAILED, _CONTRACT: AssetPartitionStatus.FAILED}},
        buckets=[_bucket("invoices", deleting=True), _bucket("contracts", ingestor="acme_ocr")],
    )

    assert not result.run_requests
    report.assert_not_called()


class TestReportOnRecord:
    """The failure is shown on the document's record, which a failed first parse of a synced file never created."""

    def _report(self, *, recorded: bool, exists: bool) -> tuple[MagicMock, MagicMock]:
        decision = IngestionRetryDecision(
            action=IngestionRetryAction.GIVE_UP,
            origin_run_id="r",
            failed_attempts=4,
            retry_number=0,
            attempt_started_at=3.9,
            failed_at=5.0,
        )
        with (
            patch(f"{_MODULE}.get_db_name_from_bucket_name", return_value="invoices_db"),
            patch(f"{_MODULE}.MongoConnectionRegistry.ensure_alias"),
            patch(f"{_MODULE}.get_or_create_namespace_for_directory", return_value="finance"),
            patch(f"{_MODULE}.RefDoc") as ref_doc,
        ):
            ref_doc.record_ingestion_failure.return_value = recorded
            ref_doc.get_existing_ids.return_value = {"x"} if exists else set()
            _report_on_record(_INVOICE, decision, encode_partition_keys=True)
        return ref_doc, ref_doc.record_ingestion_failure

    def test_a_pending_record_is_marked_given_up_if_older_than_the_attempts_start(self) -> None:
        """The start is rounded down, so a record changed within the second the attempt started is left alone."""
        ref_doc, record = self._report(recorded=True, exists=True)

        assert record.call_args.kwargs == {
            "db_alias": "invoices_db",
            "doc_id": record.call_args.kwargs["doc_id"],
            "failed_attempts": 4,
            "gave_up": True,
            "failed_at": 5,
            "attempt_started_at": 3,
        }
        ref_doc.create_placeholder.assert_not_called()

    def test_a_missing_record_gets_a_placeholder_inserted_with_the_failure(self) -> None:
        ref_doc, record = self._report(recorded=False, exists=False)

        ref_doc.create_failed_placeholder.assert_called_once_with(
            "invoices_db",
            source="s3://invoices/finance/q3.pdf",
            namespace="finance",
            failed_attempts=4,
            gave_up=True,
            failed_at=5,
        )
        assert record.call_count == 1

    def test_an_ingested_or_re_uploaded_record_is_left_alone(self) -> None:
        ref_doc, record = self._report(recorded=False, exists=True)

        ref_doc.create_failed_placeholder.assert_not_called()
        assert record.call_count == 1


class TestClearFailuresOfFreshRuns:
    """A file that changed at its source shows as processing while its new version is ingested, not as failed."""

    def _running_run(self, instance: DagsterInstance, run_id: str, partition_key: str, **tags: str) -> None:
        instance.add_run(
            DagsterRun(
                job_name="__ASSET_JOB",
                run_id=run_id,
                tags={PARTITION_NAME_TAG: partition_key, **tags},
                status=DagsterRunStatus.STARTED,
            )
        )

    def _clear(self, instance: DagsterInstance) -> MagicMock:
        with (
            patch(f"{_MODULE}.get_db_name_from_bucket_name", side_effect=lambda bucket: f"{bucket}_db"),
            patch(f"{_MODULE}.MongoConnectionRegistry.ensure_alias"),
            patch(f"{_MODULE}.RefDoc") as ref_doc,
        ):
            _clear_failures_of_fresh_runs(instance, {_INVOICE, _CONTRACT}, encode_partition_keys=True)
        return ref_doc.clear_ingestion_failures

    def test_a_fresh_run_clears_the_failure_of_its_document(self, instance) -> None:
        self._running_run(instance, "eager-run", _INVOICE)

        clear = self._clear(instance)

        clear.assert_called_once_with("invoices_db", [uri_to_id("s3://invoices/finance/q3.pdf")])

    def test_a_retry_or_another_pipelines_run_clears_nothing(self, instance) -> None:
        self._running_run(instance, "retry-run", _INVOICE, **{INGESTION_RETRY_TAG: "true"})
        self._running_run(instance, "foreign-run", make_composite_partition_key("other", "s3://other/a/b.pdf"))
        _failed_run(instance, "finished-run", _CONTRACT)

        self._clear(instance).assert_not_called()
