"""Covers what the ingestion observation does with files the listing skipped (#1927)."""

from unittest.mock import MagicMock, patch

from dagster import AssetKey, AssetMaterialization, AssetObservation

from swiss_ai_hub.pipeline.ops.data_lake.data_version_by_partition_for_data_lake import (
    SKIPPED_COUNT_METADATA_KEY,
    SKIPPED_TABLE_METADATA_KEY,
    data_version_by_partition_for_data_lake_no_op,
)
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.data_lake_listing import DataLakeListing
from swiss_ai_hub.pipeline.types.skipped_data_lake_file import SkippedDataLakeFile
from swiss_ai_hub.pipeline.util.partition_utils import make_composite_partition_key

_PATCH_TARGET = (
    "swiss_ai_hub.pipeline.ops.data_lake.data_version_by_partition_for_data_lake.replace_partition_keys_for_bucket"
)
_REASON = "Folder 'hr docs' maps to namespace 'hr_docs', which folder 'hr_docs' already owns."
_KEPT = "s3://hrdocs/hr_docs/b.md"
_SKIPPED = "s3://hrdocs/hr docs/a.md"


def _context(existing: set[str]) -> MagicMock:
    context = MagicMock()
    context.instance.get_dynamic_partitions.return_value = existing
    return context


def _partition() -> MagicMock:
    partition = MagicMock()
    partition.name = "document_ingestion_document_partitions"
    return partition


def _observe(context: MagicMock, listing: DataLakeListing) -> dict:
    return data_version_by_partition_for_data_lake_no_op(
        context=context,
        asset_key=AssetKey(["g", "data_lake"]),
        partition=_partition(),
        bucket="hrdocs",
        listing=listing,
        max_partitions=100,
    ).data_versions_by_partition


def _listing(files: list[str]) -> DataLakeListing:
    return DataLakeListing(
        files=[DataLakeFile.from_content(uri=uri, content=b"x") for uri in files],
        skipped=[SkippedDataLakeFile(uri=_SKIPPED, reason=_REASON)],
    )


@patch(_PATCH_TARGET)
def test_skipped_files_get_no_partition_and_are_reported_with_both_folders(replace: MagicMock) -> None:
    kept_key = make_composite_partition_key("hrdocs", _KEPT)
    context = _context({kept_key})

    versions = _observe(context, _listing([_KEPT]))

    assert replace.call_args.args[3] == [kept_key]
    assert list(versions) == [kept_key]
    event = context.instance.report_runless_asset_event.call_args.args[0]
    assert isinstance(event, AssetMaterialization)
    assert event.partition == kept_key
    assert event.metadata[SKIPPED_COUNT_METADATA_KEY].value == 1
    table = event.metadata[SKIPPED_TABLE_METADATA_KEY].value
    assert _SKIPPED in table and "'hr docs'" in table and "'hr_docs'" in table
    warnings = [call.args[0] for call in context.log.warning.call_args_list]
    assert any("'hr docs'" in warning and "'hr_docs'" in warning for warning in warnings)


@patch(_PATCH_TARGET)
def test_the_report_goes_out_even_when_every_file_was_skipped(replace: MagicMock) -> None:
    context = _context(set())

    versions = _observe(context, _listing([]))

    assert replace.call_args.args[3] == []
    assert versions == {}
    event = context.instance.report_runless_asset_event.call_args.args[0]
    assert isinstance(event, AssetObservation)
    assert event.partition is None
    assert event.metadata[SKIPPED_COUNT_METADATA_KEY].value == 1


@patch(_PATCH_TARGET)
def test_an_empty_data_lake_reports_nothing(_replace: MagicMock) -> None:
    context = _context(set())

    _observe(context, DataLakeListing())

    context.instance.report_runless_asset_event.assert_not_called()
    context.log.warning.assert_not_called()
