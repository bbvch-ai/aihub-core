from unittest.mock import MagicMock, PropertyMock

from aihub_pipeline.io.RcloneIOManager import RcloneIOManager
from aihub_pipeline.types.RcloneFile import MinimalRcloneFile, RcloneFile


def _make_rclone_file(name: str, path: str) -> RcloneFile:
    return RcloneFile(
        name=name,
        path=path,
        content=b"data",
        size=4,
        modified=100,
        created=100,
        remote="onedrive:Docs",
        remote_path=path,
    )


def _make_minimal_rclone_file(name: str, path: str) -> MinimalRcloneFile:
    return MinimalRcloneFile(
        name=name,
        path=path,
        size=4,
        modified=100,
    )


class TestLoadInputEncoded:
    """Verify IO manager correctly decodes partition keys when encode_partition_keys=True."""

    def test_partitioned_decodes_key(self) -> None:
        rclone_client = MagicMock()
        expected = _make_rclone_file("report, Q1.pdf", "docs/report, Q1.pdf")
        rclone_client.download_file.return_value = expected

        io_mgr = RcloneIOManager(rclone_client=rclone_client, encode_partition_keys=True)

        ctx = MagicMock()
        ctx.has_partition_key = True
        ctx.partition_key = "docs/report%2C%20Q1.pdf"

        result = io_mgr.load_input(ctx)

        assert result.name == "report, Q1.pdf"
        rclone_client.download_file.assert_called_once_with("docs/report, Q1.pdf")

    def test_partitioned_plain_key_without_encoding(self) -> None:
        rclone_client = MagicMock()
        expected = _make_rclone_file("simple.txt", "docs/simple.txt")
        rclone_client.download_file.return_value = expected

        io_mgr = RcloneIOManager(rclone_client=rclone_client, encode_partition_keys=False)

        ctx = MagicMock()
        ctx.has_partition_key = True
        ctx.partition_key = "docs/simple.txt"

        result = io_mgr.load_input(ctx)

        assert result.name == "simple.txt"
        rclone_client.download_file.assert_called_once_with("docs/simple.txt")

    def test_non_partitioned_decodes_keys_and_filters(self) -> None:
        rclone_client = MagicMock()
        all_files = [
            _make_minimal_rclone_file("report, Q1.pdf", "docs/report, Q1.pdf"),
            _make_minimal_rclone_file("other.txt", "docs/other.txt"),
        ]
        rclone_client.fetch_minimal_files.return_value = all_files

        io_mgr = RcloneIOManager(rclone_client=rclone_client, encode_partition_keys=True)

        partitions_def = MagicMock()
        partitions_def.get_partition_keys.return_value = ["docs/report%2C%20Q1.pdf"]

        ctx = MagicMock()
        ctx.has_partition_key = False
        type(ctx.upstream_output).asset_partitions_def = PropertyMock(return_value=partitions_def)
        ctx.instance = MagicMock()

        result = io_mgr.load_input(ctx)

        assert len(result) == 1
        assert result[0].name == "report, Q1.pdf"

    def test_non_partitioned_without_encoding_filters_by_path(self) -> None:
        rclone_client = MagicMock()
        all_files = [
            _make_minimal_rclone_file("simple.txt", "docs/simple.txt"),
            _make_minimal_rclone_file("other.txt", "docs/other.txt"),
        ]
        rclone_client.fetch_minimal_files.return_value = all_files

        io_mgr = RcloneIOManager(rclone_client=rclone_client, encode_partition_keys=False)

        partitions_def = MagicMock()
        partitions_def.get_partition_keys.return_value = ["docs/simple.txt"]

        ctx = MagicMock()
        ctx.has_partition_key = False
        type(ctx.upstream_output).asset_partitions_def = PropertyMock(return_value=partitions_def)
        ctx.instance = MagicMock()

        result = io_mgr.load_input(ctx)

        assert len(result) == 1
        assert result[0].name == "simple.txt"
