from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from dagster import AssetKey, DataVersionsByPartition, DynamicPartitionsDefinition

from swiss_ai_hub.pipeline.assets.factories.rclone_to_data_lake.observable_rclone_factory import (
    observable_rclone_factory,
)
from swiss_ai_hub.pipeline.types.rclone_remote import RcloneRemote

_MODULE = "swiss_ai_hub.pipeline.assets.factories.rclone_to_data_lake.observable_rclone_factory"
_BUCKET = "hrdocs"
_RUN_ID = "0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0"
_REMOTE = RcloneRemote(name="rclone_hrdocs_obs_x", fs="rclone_hrdocs_obs_x:Docs", include_patterns=["*.pdf"])


def _observe(steps: MagicMock) -> None:
    """Run the observation body with every collaborator recorded on one mock, so their order is visible."""

    @contextmanager
    def opened(bucket: str, source: str, run_id: str) -> Iterator[RcloneRemote]:
        steps.open(bucket, source, run_id)
        try:
            yield _REMOTE
        finally:
            steps.close()

    steps.data_versions.return_value = DataVersionsByPartition({})
    asset = observable_rclone_factory(
        AssetKey(["rclone_source_to_datalake", "rclone"]),
        DynamicPartitionsDefinition(name="rclone_source_partitions"),
        source="rclone",
        max_partitions=1000,
    )
    with (
        patch(f"{_MODULE}.bucket_from_run_tag", return_value=_BUCKET),
        patch(f"{_MODULE}.ObservationRcloneRemote.opened", opened),
        patch(f"{_MODULE}.build_rclone_client", return_value=MagicMock(list_files=steps.list_files)),
        patch(f"{_MODULE}.run_async", side_effect=lambda awaitable: awaitable),
        patch(f"{_MODULE}.data_version_by_partition_for_rclone_files", steps.data_versions),
        patch(f"{_MODULE}.RcloneTokenWriteBack.persist_refreshed_token", steps.write_back),
    ):
        asset.op.compute_fn.decorated_fn(MagicMock(run_id=_RUN_ID))


def _order(steps: MagicMock) -> list[str]:
    return [name for name, _, _ in steps.mock_calls if "." not in name and name]


def test_the_refreshed_token_is_written_back_after_the_data_versions_and_before_the_remote_is_deleted() -> None:
    steps = MagicMock()

    _observe(steps)

    assert _order(steps) == ["open", "list_files", "data_versions", "write_back", "close"]
    steps.open.assert_called_once_with(_BUCKET, "rclone", _RUN_ID)
    steps.list_files.assert_called_once_with(_REMOTE.fs, include=["*.pdf"], exclude=[])
    steps.write_back.assert_called_once_with(_BUCKET, "rclone", _REMOTE)


def test_a_failed_listing_writes_nothing_back_and_still_deletes_the_remote() -> None:
    steps = MagicMock()
    steps.list_files.side_effect = RuntimeError("rclone operations/list failed")

    with pytest.raises(RuntimeError, match="operations/list failed"):
        _observe(steps)

    assert _order(steps) == ["open", "list_files", "close"]
    steps.write_back.assert_not_called()
