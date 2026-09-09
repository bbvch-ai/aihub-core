from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from swiss_ai_hub.pipeline.io.routed_rclone_io_manager import RoutedRcloneIOManager
from swiss_ai_hub.pipeline.types.rclone_file import MinimalRcloneFile, RcloneFile
from swiss_ai_hub.pipeline.types.rclone_remote import RcloneRemote

_MODULE = "swiss_ai_hub.pipeline.io.routed_rclone_io_manager"
_REMOTE = RcloneRemote(name="rclone_hrdocs", fs="rclone_hrdocs:Shared", include_patterns=["*.pdf"])


def _minimal(path: str) -> MinimalRcloneFile:
    return MinimalRcloneFile(name=path.rsplit("/", 1)[-1], path=path, size=4, modified=100)


@pytest.fixture
def rclone():
    client = MagicMock()
    client.download_bytes = AsyncMock(
        return_value=RcloneFile(
            name="q1.pdf",
            path="Reports/q1.pdf",
            content=b"x",
            size=1,
            modified=1,
            created=1,
            remote="rclone_hrdocs:Shared",
            remote_path="Reports/q1.pdf",
        )
    )
    client.list_files = AsyncMock(return_value=[_minimal("Reports/q1.pdf"), _minimal("Reports/other.pdf")])
    with (
        patch(f"{_MODULE}.build_rclone_client", return_value=client),
        patch(f"{_MODULE}.rclone_remote_for_bucket", return_value=_REMOTE) as remote_for_bucket,
    ):
        yield client, remote_for_bucket


class TestPartitionedRead:
    def test_the_bucket_and_path_come_from_the_composite_key(self, rclone):
        client, remote_for_bucket = rclone
        context = MagicMock(has_partition_key=True, partition_key="hrdocs|Reports%2Fq1.pdf")

        result = RoutedRcloneIOManager(source="rclone").load_input(context)

        remote_for_bucket.assert_called_once_with("hrdocs", "rclone")
        client.download_bytes.assert_awaited_once_with("rclone_hrdocs:Shared", "Reports/q1.pdf")
        assert result.name == "q1.pdf"


class TestNonPartitionedRead:
    def test_only_this_buckets_known_partitions_are_returned(self, rclone):
        client, _ = rclone
        partitions_def = MagicMock()
        partitions_def.get_partition_keys.return_value = ["hrdocs|Reports%2Fq1.pdf", "other|Reports%2Fother.pdf"]
        context = MagicMock(has_partition_key=False)
        type(context.upstream_output).asset_partitions_def = PropertyMock(return_value=partitions_def)
        with patch(f"{_MODULE}.bucket_from_run_tag", return_value="hrdocs"):
            result = RoutedRcloneIOManager(source="rclone").load_input(context)

        client.list_files.assert_awaited_once_with("rclone_hrdocs:Shared", include=["*.pdf"], exclude=[])
        assert [file.path for file in result] == ["Reports/q1.pdf"]


class TestWrite:
    def test_sources_are_never_written_to(self):
        with pytest.raises(NotImplementedError):
            RoutedRcloneIOManager(source="rclone").handle_output(MagicMock(), object())
