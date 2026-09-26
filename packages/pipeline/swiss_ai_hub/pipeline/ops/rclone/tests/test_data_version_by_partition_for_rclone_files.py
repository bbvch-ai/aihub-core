from collections.abc import Iterator
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from dagster import AssetKey
from swiss_ai_hub.core.generative_ai.utils.path_utils import encode_partition_key

from swiss_ai_hub.pipeline.ops.rclone.data_version_by_partition_for_rclone_files import (
    data_version_by_partition_for_rclone_files,
)
from swiss_ai_hub.pipeline.types.rclone_file import MinimalRcloneFile
from swiss_ai_hub.pipeline.util.unlanded_partition_retry import UnlandedPartitionRetry
from swiss_ai_hub.pipeline.util.unlanded_partition_retry_config import UnlandedPartitionRetryConfig
from swiss_ai_hub.pipeline.util.unlanded_partitions import UnlandedPartitions
from swiss_ai_hub.pipeline.util.unlanded_partitions_report import UnlandedPartitionsReport

_PATCH_TARGET = (
    "swiss_ai_hub.pipeline.ops.rclone.data_version_by_partition_for_rclone_files.replace_partition_keys_for_bucket"
)
_RETRY_CONFIG = UnlandedPartitionRetryConfig(
    asset_key=AssetKey(["g", "data_lake_files"]), retry_job_name="retry", max_attempts=3, base_delay=timedelta(0)
)


@pytest.fixture(autouse=True)
def find_unlanded() -> Iterator[MagicMock]:
    with patch.object(UnlandedPartitions, "find", return_value=UnlandedPartitionsReport()) as find:
        yield find


def _file(path: str, modified: int = 100, size: int = 1024, hashes: dict[str, str] | None = None) -> MinimalRcloneFile:
    return MinimalRcloneFile(name=path.rsplit("/", 1)[-1], path=path, size=size, modified=modified, hashes=hashes)


def _context(existing: set[str]) -> MagicMock:
    context = MagicMock()
    context.instance.get_dynamic_partitions.return_value = existing
    return context


def _partition() -> MagicMock:
    partition = MagicMock()
    partition.name = "rclone_source_partitions"
    return partition


class TestCompositeKeys:
    @patch(_PATCH_TARGET)
    def test_keys_are_bucket_prefixed_and_reconciled_per_bucket(self, replace: MagicMock) -> None:
        file = _file("Policies/report, Q1.pdf", hashes={"md5": "abc123"})
        key = f"hrdocs|{encode_partition_key(file.path)}"
        context = _context({key})

        result = data_version_by_partition_for_rclone_files(
            context=context,
            asset_key=AssetKey(["g", "remote_files"]),
            partition=_partition(),
            bucket="hrdocs",
            rclone_files=[file],
            max_partitions=100,
            retry_config=_RETRY_CONFIG,
        )

        replace.assert_called_once_with(context, "rclone_source_partitions", "hrdocs", [key], 100)
        assert result.data_versions_by_partition[key].value == "hash:abc123"

    @patch(_PATCH_TARGET)
    def test_root_level_files_get_no_partition_and_are_counted(self, replace: MagicMock) -> None:
        nested = _file("Policies/handbook.pdf", hashes={"md5": "x"})
        context = _context({f"hrdocs|{encode_partition_key(nested.path)}"})

        data_version_by_partition_for_rclone_files(
            context=context,
            asset_key=AssetKey(["g", "remote_files"]),
            partition=_partition(),
            bucket="hrdocs",
            rclone_files=[_file("readme.txt"), nested],
            max_partitions=100,
            retry_config=_RETRY_CONFIG,
        )

        keys = replace.call_args.args[3]
        assert keys == [f"hrdocs|{encode_partition_key(nested.path)}"]
        materialization = context.instance.report_runless_asset_event.call_args.args[0]
        assert materialization.metadata["Skipped root-level files"].value == 1
        assert materialization.metadata["Bucket"].value == "hrdocs"


class TestDataVersions:
    @patch(_PATCH_TARGET)
    def test_files_without_a_partition_yet_are_versioned_on_the_next_observation(self, replace: MagicMock) -> None:
        file = _file("a/new.pdf", hashes={"md5": "x"})

        result = data_version_by_partition_for_rclone_files(
            context=_context(set()),
            asset_key=AssetKey(["g", "remote_files"]),
            partition=_partition(),
            bucket="hrdocs",
            rclone_files=[file],
            max_partitions=100,
            retry_config=_RETRY_CONFIG,
        )

        assert result.data_versions_by_partition == {}

    @patch(_PATCH_TARGET)
    def test_mtime_and_size_version_backends_without_hashes(self, replace: MagicMock) -> None:
        file = _file("a/plain.pdf", modified=5, size=9)
        key = f"hrdocs|{encode_partition_key(file.path)}"

        result = data_version_by_partition_for_rclone_files(
            context=_context({key}),
            asset_key=AssetKey(["g", "remote_files"]),
            partition=_partition(),
            bucket="hrdocs",
            rclone_files=[file],
            max_partitions=100,
            retry_config=_RETRY_CONFIG,
        )

        assert result.data_versions_by_partition[key].value == "mtime:5-9"


class TestUnlandedFiles:
    @staticmethod
    def _observe(context: MagicMock, files: list[MinimalRcloneFile]) -> None:
        data_version_by_partition_for_rclone_files(
            context=context,
            asset_key=AssetKey(["g", "remote_files"]),
            partition=_partition(),
            bucket="hrdocs",
            rclone_files=files,
            max_partitions=100,
            retry_config=_RETRY_CONFIG,
        )

    @patch(_PATCH_TARGET)
    def test_counts_are_reported_in_the_observation_metadata(self, replace: MagicMock, find_unlanded) -> None:
        find_unlanded.return_value = UnlandedPartitionsReport(
            to_retry=[UnlandedPartitionRetry(partition_key="hrdocs|a", attempt=1, run_number=0)],
            exhausted=["hrdocs|b"],
        )
        context = _context(set())

        self._observe(context, [_file("a/one.pdf")])

        metadata = context.instance.report_runless_asset_event.call_args.args[0].metadata
        assert metadata["Missing from data lake"].value == 2
        assert metadata["Retries exhausted"].value == 1
        context.log.warning.assert_called_once()

    @patch(_PATCH_TARGET)
    def test_metadata_is_emitted_without_nested_files(self, replace: MagicMock) -> None:
        context = _context(set())

        self._observe(context, [_file("readme.txt")])

        materialization = context.instance.report_runless_asset_event.call_args.args[0]
        assert materialization.partition is None
        assert materialization.metadata["Missing from data lake"].value == 0
        assert materialization.metadata["Retries exhausted"].value == 0
        assert materialization.metadata["Number of Files"].value == 0

    @patch(_PATCH_TARGET)
    def test_only_keys_that_existed_before_and_still_exist_are_inspected(
        self, replace: MagicMock, find_unlanded
    ) -> None:
        """A key added by this observation has had no run yet; a key it removed is gone."""
        kept = f"hrdocs|{encode_partition_key('a/kept.pdf')}"
        context = _context({kept, "hrdocs|removed.pdf", "finance|a%2Fkept.pdf"})

        self._observe(context, [_file("a/kept.pdf"), _file("a/new.pdf")])

        assert find_unlanded.call_args.args[3] == [kept]
