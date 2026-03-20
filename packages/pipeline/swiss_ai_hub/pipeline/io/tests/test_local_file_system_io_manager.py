from pathlib import Path
from unittest.mock import MagicMock, PropertyMock

from swiss_ai_hub.pipeline.io.local_file_system_io_manager import LocalFileSystemIOManager
from swiss_ai_hub.pipeline.resources.local_file_system.local_file_system_resource import LocalFileSystemResource


def _make_io_manager(base_path: str, encode: bool = False) -> LocalFileSystemIOManager:
    client = LocalFileSystemResource(
        base_path=base_path,
        include_patterns=None,
        exclude_patterns=None,
    )
    return LocalFileSystemIOManager(
        local_file_system_client=client,
        encode_partition_keys=encode,
    )


def _make_input_context(partition_key: str) -> MagicMock:
    ctx = MagicMock()
    ctx.has_partition_key = True
    ctx.partition_key = partition_key
    return ctx


class TestLoadInputEncoded:
    """Verify IO manager correctly decodes partition keys when encode_partition_keys=True."""

    def test_partitioned_decodes_key(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "report, Q1.pdf").write_bytes(b"data")

        io_mgr = _make_io_manager(str(tmp_path), encode=True)
        ctx = _make_input_context("docs/report%2C%20Q1.pdf")

        result = io_mgr.load_input(ctx)

        assert result.name == "report, Q1.pdf"
        assert result.content == b"data"

    def test_partitioned_plain_key_without_encoding(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "simple.txt").write_bytes(b"text")

        io_mgr = _make_io_manager(str(tmp_path), encode=False)
        ctx = _make_input_context("docs/simple.txt")

        result = io_mgr.load_input(ctx)

        assert result.name == "simple.txt"
        assert result.content == b"text"

    def test_non_partitioned_encoded_filters_by_decoded_path(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "report, Q1.pdf").write_bytes(b"data1")
        (docs / "file 2.txt").write_bytes(b"data2")
        (docs / "other.txt").write_bytes(b"data3")

        io_mgr = _make_io_manager(str(tmp_path), encode=True)

        partitions_def = MagicMock()
        partitions_def.get_partition_keys.return_value = [
            "docs/report%2C%20Q1.pdf",
            "docs/file%202.txt",
        ]

        ctx = MagicMock()
        ctx.has_partition_key = False
        type(ctx.upstream_output).asset_partitions_def = PropertyMock(return_value=partitions_def)
        ctx.instance = MagicMock()

        result = io_mgr.load_input(ctx)

        assert len(result) == 2
        names = {f.name for f in result}
        assert names == {"report, Q1.pdf", "file 2.txt"}

    def test_non_partitioned_without_encoding_filters_by_path(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "simple.txt").write_bytes(b"data1")
        (docs / "other.txt").write_bytes(b"data2")

        io_mgr = _make_io_manager(str(tmp_path), encode=False)

        partitions_def = MagicMock()
        partitions_def.get_partition_keys.return_value = ["docs/simple.txt"]

        ctx = MagicMock()
        ctx.has_partition_key = False
        type(ctx.upstream_output).asset_partitions_def = PropertyMock(return_value=partitions_def)
        ctx.instance = MagicMock()

        result = io_mgr.load_input(ctx)

        assert len(result) == 1
        assert result[0].name == "simple.txt"
