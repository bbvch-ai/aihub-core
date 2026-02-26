from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from aihub_lib.generative_ai.utils.path_utils import encode_partition_key
from dagster import AssetKey

from aihub_pipeline.ops.data_lake.data_version_by_partition_for_data_lake_files import (
    data_version_by_partition_for_data_lake_files_no_op,
)
from aihub_pipeline.types.DataLakeFile import DataLakeFile

_NOW = int(datetime.now(tz=UTC).timestamp())


def _make_file(uri: str, updated: int = 100, file_hash: str = "abc") -> DataLakeFile:
    name = uri.rsplit("/", 1)[-1]
    return DataLakeFile(
        name=name,
        namespace="docs",
        filetype="pdf",
        uri=uri,
        size=1024,
        created=_NOW,
        updated=updated,
        content_type="application/pdf",
        owner="test",
        hash=file_hash,
        metadata={},
    )


def _make_context(existing_partitions: set[str]) -> MagicMock:
    ctx = MagicMock()
    ctx.instance.get_dynamic_partitions.return_value = existing_partitions
    return ctx


_PATCH_TARGET = "aihub_pipeline.ops.data_lake.data_version_by_partition_for_data_lake_files.replace_partition_keys"


class TestDataVersionByPartitionForDataLakeFiles:
    @patch(_PATCH_TARGET)
    def test_encode_true_produces_encoded_keys(self, mock_replace: MagicMock) -> None:
        file = _make_file("s3://bucket/docs/report, Q1.pdf", updated=100, file_hash="abc")
        encoded = encode_partition_key(file.uri)
        ctx = _make_context({encoded})
        partition = MagicMock()
        partition.name = "test_partitions"

        result = data_version_by_partition_for_data_lake_files_no_op(
            context=ctx,
            asset_key=AssetKey(["test", "data_lake"]),
            partition=partition,
            data_lake_files=[file],
            max_partitions=100,
            encode_partition_keys=True,
        )

        mock_replace.assert_called_once_with(ctx, "test_partitions", [encoded], max_partitions=100)
        assert encoded in result.data_versions_by_partition
        assert result.data_versions_by_partition[encoded].value == "100-abc"

    @patch(_PATCH_TARGET)
    def test_encode_false_produces_raw_keys(self, mock_replace: MagicMock) -> None:
        file = _make_file("s3://bucket/docs/report.pdf", updated=200, file_hash="def")
        ctx = _make_context({file.uri})
        partition = MagicMock()
        partition.name = "test_partitions"

        result = data_version_by_partition_for_data_lake_files_no_op(
            context=ctx,
            asset_key=AssetKey(["test", "data_lake"]),
            partition=partition,
            data_lake_files=[file],
            max_partitions=100,
            encode_partition_keys=False,
        )

        mock_replace.assert_called_once_with(ctx, "test_partitions", [file.uri], max_partitions=100)
        assert file.uri in result.data_versions_by_partition

    @patch(_PATCH_TARGET)
    def test_filters_to_existing_partitions(self, mock_replace: MagicMock) -> None:
        file1 = _make_file("s3://bucket/docs/a.pdf", updated=100, file_hash="h1")
        file2 = _make_file("s3://bucket/docs/b.pdf", updated=200, file_hash="h2")
        ctx = _make_context({file1.uri})
        partition = MagicMock()
        partition.name = "test_partitions"

        result = data_version_by_partition_for_data_lake_files_no_op(
            context=ctx,
            asset_key=AssetKey(["test", "data_lake"]),
            partition=partition,
            data_lake_files=[file1, file2],
            max_partitions=100,
            encode_partition_keys=False,
        )

        assert file1.uri in result.data_versions_by_partition
        assert file2.uri not in result.data_versions_by_partition

    @patch(_PATCH_TARGET)
    def test_empty_files_list(self, mock_replace: MagicMock) -> None:
        ctx = _make_context(set())
        partition = MagicMock()
        partition.name = "test_partitions"

        result = data_version_by_partition_for_data_lake_files_no_op(
            context=ctx,
            asset_key=AssetKey(["test", "data_lake"]),
            partition=partition,
            data_lake_files=[],
            max_partitions=100,
            encode_partition_keys=True,
        )

        ctx.instance.report_runless_asset_event.assert_not_called()
        assert len(result.data_versions_by_partition) == 0
