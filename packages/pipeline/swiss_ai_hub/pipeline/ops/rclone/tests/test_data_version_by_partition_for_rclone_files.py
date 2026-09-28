from unittest.mock import MagicMock, patch

from dagster import AssetKey
from swiss_ai_hub.core.generative_ai.utils.path_utils import encode_partition_key

from swiss_ai_hub.pipeline.ops.rclone.data_version_by_partition_for_rclone_files import (
    data_version_by_partition_for_rclone_files,
)
from swiss_ai_hub.pipeline.types.rclone_file import MinimalRcloneFile

_PATCH_TARGET = (
    "swiss_ai_hub.pipeline.ops.rclone.data_version_by_partition_for_rclone_files.replace_partition_keys_for_bucket"
)


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
        )

        assert result.data_versions_by_partition[key].value == "mtime:5-9"
