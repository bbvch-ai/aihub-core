from unittest.mock import MagicMock, patch

from dagster import AssetKey
from swiss_ai_hub.core.generative_ai.utils.path_utils import encode_partition_key

from swiss_ai_hub.pipeline.ops.local_file_system.data_version_by_partition_for_local_files import (
    data_version_by_partition_for_local_files,
)
from swiss_ai_hub.pipeline.types.SourceFile import MinimalSourceFile


def _make_file(path: str, modified: int = 100, size: int = 1024) -> MinimalSourceFile:
    name = path.rsplit("/", 1)[-1]
    return MinimalSourceFile(name=name, path=path, size=size, modified=modified)


def _make_context(existing_partitions: set[str]) -> MagicMock:
    ctx = MagicMock()
    ctx.instance.get_dynamic_partitions.return_value = existing_partitions
    return ctx


_PATCH_TARGET = (
    "swiss_ai_hub.pipeline.ops.local_file_system.data_version_by_partition_for_local_files.replace_partition_keys"
)


class TestDataVersionByPartitionForLocalFiles:
    @patch(_PATCH_TARGET)
    def test_encode_true_produces_encoded_keys(self, mock_replace: MagicMock) -> None:
        file = _make_file("docs/report, Q1.pdf", modified=100, size=1024)
        encoded = encode_partition_key(file.path)
        ctx = _make_context({encoded})
        partition = MagicMock()
        partition.name = "test_partitions"

        result = data_version_by_partition_for_local_files(
            context=ctx,
            asset_key=AssetKey(["test", "local_fs"]),
            partition=partition,
            local_files=[file],
            max_partitions=100,
            encode_partition_keys=True,
        )

        mock_replace.assert_called_once_with(ctx, "test_partitions", [encoded], max_partitions=100)
        assert encoded in result.data_versions_by_partition
        assert result.data_versions_by_partition[encoded].value == "100-1024"

    @patch(_PATCH_TARGET)
    def test_encode_false_produces_raw_keys(self, mock_replace: MagicMock) -> None:
        file = _make_file("docs/report.pdf", modified=200, size=2048)
        ctx = _make_context({file.path})
        partition = MagicMock()
        partition.name = "test_partitions"

        result = data_version_by_partition_for_local_files(
            context=ctx,
            asset_key=AssetKey(["test", "local_fs"]),
            partition=partition,
            local_files=[file],
            max_partitions=100,
            encode_partition_keys=False,
        )

        mock_replace.assert_called_once_with(ctx, "test_partitions", [file.path], max_partitions=100)
        assert file.path in result.data_versions_by_partition

    @patch(_PATCH_TARGET)
    def test_filters_to_existing_partitions(self, mock_replace: MagicMock) -> None:
        file1 = _make_file("docs/a.pdf", modified=100, size=1024)
        file2 = _make_file("docs/b.pdf", modified=200, size=2048)
        ctx = _make_context({file1.path})
        partition = MagicMock()
        partition.name = "test_partitions"

        result = data_version_by_partition_for_local_files(
            context=ctx,
            asset_key=AssetKey(["test", "local_fs"]),
            partition=partition,
            local_files=[file1, file2],
            max_partitions=100,
            encode_partition_keys=False,
        )

        assert file1.path in result.data_versions_by_partition
        assert file2.path not in result.data_versions_by_partition

    @patch(_PATCH_TARGET)
    def test_empty_files_list(self, mock_replace: MagicMock) -> None:
        ctx = _make_context(set())
        partition = MagicMock()
        partition.name = "test_partitions"

        result = data_version_by_partition_for_local_files(
            context=ctx,
            asset_key=AssetKey(["test", "local_fs"]),
            partition=partition,
            local_files=[],
            max_partitions=100,
            encode_partition_keys=True,
        )

        ctx.instance.report_runless_asset_event.assert_not_called()
        assert len(result.data_versions_by_partition) == 0
