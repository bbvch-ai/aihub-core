from unittest.mock import MagicMock

from swiss_ai_hub.pipeline.util.partition_utils import (
    bucket_of_composite_partition_key,
    make_composite_partition_key,
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
