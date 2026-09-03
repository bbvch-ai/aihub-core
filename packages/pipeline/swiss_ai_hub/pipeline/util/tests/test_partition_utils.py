from unittest.mock import MagicMock

from swiss_ai_hub.pipeline.util.partition_utils import PARTITIONS_TRUNCATED_TAG, replace_partition_keys

_PARTITION_NAME = "bucket_document_partitions"


def _context(existing_keys: list[str]) -> MagicMock:
    context = MagicMock()
    context.run_id = "run-abc"
    context.instance.get_dynamic_partitions.return_value = existing_keys
    return context


class TestTruncationSignalling:
    def test_a_batch_within_the_cap_is_not_tagged(self) -> None:
        context = _context([])

        replace_partition_keys(context, _PARTITION_NAME, [f"key{index}" for index in range(10)], max_partitions=10)

        context.instance.add_run_tags.assert_not_called()
        context.log.warning.assert_not_called()

    def test_truncated_additions_tag_the_run(self) -> None:
        """The sensor runs in another process and cannot read this run's state, so the fact that
        the partition set did not converge has to travel back as a run tag."""
        context = _context([])

        replace_partition_keys(context, _PARTITION_NAME, [f"key{index}" for index in range(15)], max_partitions=10)

        context.instance.add_run_tags.assert_called_once_with("run-abc", PARTITIONS_TRUNCATED_TAG)
        context.log.warning.assert_called_once()

    def test_truncated_deletions_tag_the_run(self) -> None:
        context = _context([f"key{index}" for index in range(15)])

        replace_partition_keys(context, _PARTITION_NAME, [], max_partitions=10)

        context.instance.add_run_tags.assert_called_once_with("run-abc", PARTITIONS_TRUNCATED_TAG)

    def test_additions_are_still_capped(self) -> None:
        context = _context([])

        replace_partition_keys(context, _PARTITION_NAME, [f"key{index}" for index in range(15)], max_partitions=10)

        added = context.instance.add_dynamic_partitions.call_args.kwargs["partition_keys"]
        assert len(added) == 10
