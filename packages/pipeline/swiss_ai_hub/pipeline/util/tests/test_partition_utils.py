from unittest.mock import MagicMock

from swiss_ai_hub.pipeline.util.partition_utils import (
    PARTITIONS_TRUNCATED_TAG,
    bucket_of_composite_partition_key,
    make_composite_partition_key,
    replace_partition_keys,
    replace_partition_keys_for_bucket,
    split_composite_partition_key,
)


def test_composite_key_round_trip_with_special_characters():
    uri = "s3://mybucket/folder/file with spaces & symbols|pipe.pdf"
    key = make_composite_partition_key("mybucket", uri)

    # The separator only appears once: literal '|' in the URI is percent-encoded.
    assert key.count("|") == 1
    assert key.startswith("mybucket|")

    bucket, decoded_uri = split_composite_partition_key(key)
    assert bucket == "mybucket"
    assert decoded_uri == uri
    assert bucket_of_composite_partition_key(key) == "mybucket"


def test_make_composite_key_without_encoding():
    key = make_composite_partition_key("b", "s3://b/x.pdf", encode=False)
    assert key == "b|s3://b/x.pdf"
    assert split_composite_partition_key(key, encode=False) == ("b", "s3://b/x.pdf")


def test_replace_partition_keys_for_bucket_only_touches_its_own_bucket():
    existing = [
        "bucketa|s3:%2F%2Fbucketa%2Fold.pdf",
        "bucketa|s3:%2F%2Fbucketa%2Fkeep.pdf",
        "bucketb|s3:%2F%2Fbucketb%2Funrelated.pdf",
    ]
    context = MagicMock()
    context.instance.get_dynamic_partitions.return_value = existing

    new_keys = [
        "bucketa|s3:%2F%2Fbucketa%2Fkeep.pdf",
        "bucketa|s3:%2F%2Fbucketa%2Fnew.pdf",
    ]
    replace_partition_keys_for_bucket(context, "shared_registry", "bucketa", new_keys, max_partitions=1000)

    context.instance.add_dynamic_partitions.assert_called_once()
    added = context.instance.add_dynamic_partitions.call_args.kwargs["partition_keys"]
    assert added == ["bucketa|s3:%2F%2Fbucketa%2Fnew.pdf"]

    deleted = [call.kwargs["partition_key"] for call in context.instance.delete_dynamic_partition.call_args_list]
    # Only bucketa's stale key is deleted; bucketb's key is never touched.
    assert deleted == ["bucketa|s3:%2F%2Fbucketa%2Fold.pdf"]


def test_replace_partition_keys_for_bucket_respects_max_partitions():
    context = MagicMock()
    context.instance.get_dynamic_partitions.return_value = []
    new_keys = [f"b|key{i}" for i in range(5)]

    replace_partition_keys_for_bucket(context, "reg", "b", new_keys, max_partitions=2)

    added = context.instance.add_dynamic_partitions.call_args.kwargs["partition_keys"]
    assert len(added) == 2


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
