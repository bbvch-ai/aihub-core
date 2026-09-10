import warnings
from unittest.mock import patch

from swiss_ai_hub.pipeline.util.definitions_util import (
    default_rclone_to_datalake_definitions,
    resolve_encode_partition_keys,
)


class TestResolveEncodePartitionKeys:
    def test_true_returns_true(self) -> None:
        assert resolve_encode_partition_keys(True) is True

    def test_false_returns_false(self) -> None:
        assert resolve_encode_partition_keys(False) is False

    def test_none_returns_false_with_deprecation_warning(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = resolve_encode_partition_keys(None)
            assert result is False
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "encode_partition_keys" in str(w[0].message)


class TestRclonePipelinePartitionNaming:
    """Regression test for issue #1236: two rclone pipelines registered in the same
    Dagster instance must produce distinct ``DynamicPartitionsDefinition`` names so
    that their partition state does not collide."""

    @patch("swiss_ai_hub.pipeline.util.definitions_util.get_db_name_from_bucket_name")
    def test_two_rclone_pipelines_have_distinct_partition_names(self, mock_get_db_name) -> None:
        mock_get_db_name.side_effect = lambda bucket_name, **_: bucket_name

        defs_a = default_rclone_to_datalake_definitions(
            datalake_container_name="bucket_a",
            source_remote="onedrive:Docs",
            encode_partition_keys=False,
        )
        defs_b = default_rclone_to_datalake_definitions(
            datalake_container_name="bucket_a",
            source_remote="gdrive:Shared",
            encode_partition_keys=False,
        )

        assert defs_a.assets[0].partitions_def.name != defs_b.assets[0].partitions_def.name
