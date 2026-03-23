from datetime import UTC, datetime
from unittest.mock import MagicMock, PropertyMock

from swiss_ai_hub.pipeline.io.s3_data_lake_io_manager import S3DataLakeIOManager
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile


def _make_data_lake_file(name: str, namespace: str, uri: str, **kwargs) -> DataLakeFile:
    now = datetime.now(tz=UTC)
    defaults = {
        "filetype": name.rsplit(".", 1)[-1] if "." in name else "bin",
        "size": 1024,
        "created": int(now.timestamp()),
        "updated": int(now.timestamp()),
        "content_type": "application/octet-stream",
        "owner": "test",
        "hash": "abc123",
        "metadata": {},
    }
    defaults.update(kwargs)
    return DataLakeFile(name=name, namespace=namespace, uri=uri, **defaults)


def _make_s3_client() -> MagicMock:
    """Create a mocked S3DataLakeClient."""
    mock = MagicMock()

    mock.create_data_lake_file_from_uri.return_value = _make_data_lake_file(
        "simple.txt", "docs", "s3://bucket/docs/simple.txt", content_type="text/plain", hash="def456"
    )

    mock.build_uri.side_effect = lambda path: f"s3://bucket/{path}"

    return mock


class TestLoadInputEncoded:
    """Verify IO manager correctly decodes partition keys when encode_partition_keys=True."""

    def test_partitioned_decodes_key_and_loads_from_uri(self) -> None:
        s3_client = _make_s3_client()
        s3_client.create_data_lake_file_from_uri.return_value = _make_data_lake_file(
            "report, Q1.pdf", "docs", "s3://bucket/docs/report, Q1.pdf", content_type="application/pdf"
        )
        fs = MagicMock()

        io_mgr = S3DataLakeIOManager(
            data_lake_client=s3_client,
            data_lake_file_system=fs,
            encode_partition_keys=True,
        )

        ctx = MagicMock()
        ctx.has_partition_key = True
        ctx.partition_key = "s3://bucket/docs/report%2C%20Q1.pdf"
        ctx.log = MagicMock()

        result = io_mgr.load_input(ctx)

        assert result.name == "report, Q1.pdf"
        s3_client.create_data_lake_file_from_uri.assert_called_once_with("s3://bucket/docs/report, Q1.pdf")

    def test_partitioned_uses_uri_directly_without_encoding(self) -> None:
        s3_client = _make_s3_client()
        fs = MagicMock()

        io_mgr = S3DataLakeIOManager(
            data_lake_client=s3_client,
            data_lake_file_system=fs,
            encode_partition_keys=False,
        )

        ctx = MagicMock()
        ctx.has_partition_key = True
        ctx.partition_key = "s3://bucket/docs/simple.txt"
        ctx.log = MagicMock()

        result = io_mgr.load_input(ctx)

        assert result.name == "simple.txt"
        s3_client.create_data_lake_file_from_uri.assert_called_once_with("s3://bucket/docs/simple.txt")

    def test_non_partitioned_encoded_decodes_each_key(self) -> None:
        s3_client = _make_s3_client()
        s3_client.create_data_lake_file_from_uri.return_value = _make_data_lake_file(
            "report, Q1.pdf", "docs", "s3://bucket/docs/report, Q1.pdf", content_type="application/pdf"
        )
        fs = MagicMock()

        io_mgr = S3DataLakeIOManager(
            data_lake_client=s3_client,
            data_lake_file_system=fs,
            encode_partition_keys=True,
        )

        partitions_def = MagicMock()
        partitions_def.get_partition_keys.return_value = [
            "s3://bucket/docs/report%2C%20Q1.pdf",
        ]

        ctx = MagicMock()
        ctx.has_partition_key = False
        type(ctx.upstream_output).asset_partitions_def = PropertyMock(return_value=partitions_def)
        ctx.instance = MagicMock()
        ctx.log = MagicMock()

        result = io_mgr.load_input(ctx)

        assert len(result) == 1
        assert result[0].name == "report, Q1.pdf"
        s3_client.create_data_lake_file_from_uri.assert_called_once_with("s3://bucket/docs/report, Q1.pdf")

    def test_non_partitioned_without_encoding_loads_each_key(self) -> None:
        s3_client = _make_s3_client()
        fs = MagicMock()

        io_mgr = S3DataLakeIOManager(
            data_lake_client=s3_client,
            data_lake_file_system=fs,
            encode_partition_keys=False,
        )

        partitions_def = MagicMock()
        partitions_def.get_partition_keys.return_value = ["s3://bucket/docs/simple.txt"]

        ctx = MagicMock()
        ctx.has_partition_key = False
        type(ctx.upstream_output).asset_partitions_def = PropertyMock(return_value=partitions_def)
        ctx.instance = MagicMock()
        ctx.log = MagicMock()

        result = io_mgr.load_input(ctx)

        assert len(result) == 1
        assert result[0].name == "simple.txt"
        s3_client.create_data_lake_file_from_uri.assert_called_once_with("s3://bucket/docs/simple.txt")
