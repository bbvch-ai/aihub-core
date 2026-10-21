from unittest.mock import MagicMock, patch

import pytest
from dagster import AssetKey, DataVersionsByPartition, DynamicPartitionsDefinition
from swiss_ai_hub.core.persistence import MilvusPartitionState

from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.observable_data_lake_factory import (
    observable_data_lake_factory,
)
from swiss_ai_hub.pipeline.types.default_partition_repair_report import DefaultPartitionRepairReport

_MODULE = "swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.observable_data_lake_factory"

BUCKET = "handbook"


def _observe(repair_report: DefaultPartitionRepairReport) -> tuple[MagicMock, MagicMock]:
    """Run the observation body with every collaborator recorded on one mock, so their order is visible."""
    steps = MagicMock()
    steps.repair.return_value = repair_report
    steps.register_partitions.return_value = DataVersionsByPartition({})
    context = MagicMock()
    asset = observable_data_lake_factory(
        AssetKey(["document_ingestion_datalake_to_vectorstore", "data_lake"]),
        DynamicPartitionsDefinition(name="document_ingestion_document_partitions"),
        max_partitions=1000,
    )
    with (
        patch(f"{_MODULE}.bucket_from_run_tag", return_value=BUCKET),
        patch(f"{_MODULE}.DefaultPartitionRepairService.repair", steps.repair),
        patch(f"{_MODULE}.build_s3_data_lake_client", steps.build_s3_data_lake_client),
        patch(f"{_MODULE}.fetch_all_files_in_data_lake_no_op", steps.fetch_all_files),
        patch(f"{_MODULE}.data_version_by_partition_for_data_lake_no_op", steps.register_partitions),
    ):
        asset.op.compute_fn.decorated_fn(context)
    return steps, context


def test_the_vector_collection_is_provisioned_before_any_document_partition_is_registered() -> None:
    """A document partition is what starts an ingestion run, so none may exist before its collection is complete."""
    steps, _ = _observe(DefaultPartitionRepairReport(partition_state=MilvusPartitionState.COMPLETE))

    called = [name for name, _, _ in steps.mock_calls if name in {"repair", "register_partitions"}]
    assert called == ["repair", "register_partitions"]
    steps.repair.assert_called_once_with(BUCKET)


@pytest.mark.parametrize(
    ("report", "warned"),
    [
        (DefaultPartitionRepairReport(partition_state=MilvusPartitionState.COMPLETE), False),
        (
            DefaultPartitionRepairReport(
                partition_state=MilvusPartitionState.COMPLETE, moved_nodes=3, document_ids=["doc1"]
            ),
            True,
        ),
    ],
)
def test_a_repair_that_changed_anything_is_logged_as_a_warning(
    report: DefaultPartitionRepairReport, warned: bool
) -> None:
    _, context = _observe(report)

    assert context.log.warning.called is warned
