from unittest.mock import MagicMock, patch

from aihub_lib.generative_ai.utils.path_utils import encode_partition_key
from dagster import AssetKey

from aihub_pipeline.ops.rclone.data_version_by_partition_for_rclone_files import (
    data_version_by_partition_for_rclone_files,
)
from aihub_pipeline.types.RcloneFile import MinimalRcloneFile


def _make_file(
    path: str,
    modified: int = 100,
    size: int = 1024,
    hashes: dict[str, str] | None = None,
) -> MinimalRcloneFile:
    name = path.rsplit("/", 1)[-1]
    return MinimalRcloneFile(name=name, path=path, size=size, modified=modified, hashes=hashes)


def _make_context(existing_partitions: set[str]) -> MagicMock:
    ctx = MagicMock()
    ctx.instance.get_dynamic_partitions.return_value = existing_partitions
    return ctx


_PATCH_TARGET = "aihub_pipeline.ops.rclone.data_version_by_partition_for_rclone_files.replace_partition_keys"


class TestDataVersionByPartitionForRcloneFiles:
    @patch(_PATCH_TARGET)
    def test_encode_true_produces_encoded_keys(self, mock_replace: MagicMock) -> None:
        file = _make_file("docs/report, Q1.pdf", hashes={"md5": "abc123"})
        encoded = encode_partition_key(file.path)
        ctx = _make_context({encoded})
        partition = MagicMock()
        partition.name = "test_partitions"

        result = data_version_by_partition_for_rclone_files(
            context=ctx,
            asset_key=AssetKey(["test", "rclone"]),
            partition=partition,
            rclone_files=[file],
            max_partitions=100,
            encode_partition_keys=True,
        )

        mock_replace.assert_called_once_with(ctx, "test_partitions", [encoded], max_partitions=100)
        assert encoded in result.data_versions_by_partition
        assert result.data_versions_by_partition[encoded].value == "hash:abc123"

    @patch(_PATCH_TARGET)
    def test_encode_false_produces_raw_keys(self, mock_replace: MagicMock) -> None:
        file = _make_file("docs/report.pdf", hashes={"md5": "def456"})
        ctx = _make_context({file.path})
        partition = MagicMock()
        partition.name = "test_partitions"

        result = data_version_by_partition_for_rclone_files(
            context=ctx,
            asset_key=AssetKey(["test", "rclone"]),
            partition=partition,
            rclone_files=[file],
            max_partitions=100,
            encode_partition_keys=False,
        )

        mock_replace.assert_called_once_with(ctx, "test_partitions", [file.path], max_partitions=100)
        assert file.path in result.data_versions_by_partition

    @patch(_PATCH_TARGET)
    def test_filters_to_existing_partitions(self, mock_replace: MagicMock) -> None:
        file1 = _make_file("docs/a.pdf", hashes={"md5": "h1"})
        file2 = _make_file("docs/b.pdf", hashes={"md5": "h2"})
        ctx = _make_context({file1.path})
        partition = MagicMock()
        partition.name = "test_partitions"

        result = data_version_by_partition_for_rclone_files(
            context=ctx,
            asset_key=AssetKey(["test", "rclone"]),
            partition=partition,
            rclone_files=[file1, file2],
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

        result = data_version_by_partition_for_rclone_files(
            context=ctx,
            asset_key=AssetKey(["test", "rclone"]),
            partition=partition,
            rclone_files=[],
            max_partitions=100,
            encode_partition_keys=True,
        )

        ctx.instance.report_runless_asset_event.assert_not_called()
        assert len(result.data_versions_by_partition) == 0

    @patch(_PATCH_TARGET)
    def test_hash_based_vs_mtime_based_versioning(self, mock_replace: MagicMock) -> None:
        """Files with hashes use hash-based version; files without use mtime+size fallback."""
        file_with_hash = _make_file("docs/a.pdf", modified=100, size=1024, hashes={"md5": "abc"})
        file_without_hash = _make_file("docs/b.pdf", modified=200, size=2048, hashes=None)
        ctx = _make_context({file_with_hash.path, file_without_hash.path})
        partition = MagicMock()
        partition.name = "test_partitions"

        result = data_version_by_partition_for_rclone_files(
            context=ctx,
            asset_key=AssetKey(["test", "rclone"]),
            partition=partition,
            rclone_files=[file_with_hash, file_without_hash],
            max_partitions=100,
            encode_partition_keys=False,
        )

        assert result.data_versions_by_partition[file_with_hash.path].value == "hash:abc"
        assert result.data_versions_by_partition[file_without_hash.path].value == "mtime:200-2048"
