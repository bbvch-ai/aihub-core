from dagster import OpExecutionContext
from swiss_ai_hub.core.generative_ai.utils.path_utils import decode_partition_key, encode_partition_key

COMPOSITE_PARTITION_KEY_SEPARATOR = "|"
PARTITIONS_TRUNCATED_TAG = {"partitions-truncated": "true"}


def make_composite_partition_key(bucket: str, file_uri: str, *, encode: bool = True) -> str:
    """Build a bucket-scoped composite partition key ``{bucket}|{encoded_file_uri}``.

    The single RAG pipeline shares one dynamic-partition registry across all knowledge databases, so the
    bucket must be part of every key. It is prefixed rather than parsed back out of the URI — which does
    contain it — so that the key's semantics are ``(bucket, file)`` and extracting the bucket needs no
    knowledge of the storage backend's URI grammar. Bucket names are alphanumeric and
    ``encode_partition_key`` percent-encodes any literal ``|`` in the URI, so the first ``|`` always
    separates the two.
    """
    encoded = encode_partition_key(file_uri) if encode else file_uri
    return f"{bucket}{COMPOSITE_PARTITION_KEY_SEPARATOR}{encoded}"


def split_composite_partition_key(partition_key: str, *, encode: bool = True) -> tuple[str, str]:
    """Split a composite partition key back into ``(bucket, file_uri)``."""
    bucket, encoded = partition_key.split(COMPOSITE_PARTITION_KEY_SEPARATOR, 1)
    file_uri = decode_partition_key(encoded) if encode else encoded
    return bucket, file_uri


def bucket_of_composite_partition_key(partition_key: str) -> str:
    """Return the bucket component of a composite partition key without decoding the file URI."""
    return partition_key.split(COMPOSITE_PARTITION_KEY_SEPARATOR, 1)[0]


def replace_partition_keys_for_bucket(
    context: OpExecutionContext,
    partition_name: str,
    bucket: str,
    keys: list[str],
    max_partitions: int,
):
    """Reconcile dynamic partition keys for a single bucket within a shared registry.

    Only keys belonging to ``bucket`` (prefix ``{bucket}|``) are considered for deletion, so one bucket's
    observe run can never delete another bucket's partitions. ``keys`` must already be composite keys.
    """
    new_keys_set = set(keys)
    bucket_prefix = f"{bucket}{COMPOSITE_PARTITION_KEY_SEPARATOR}"
    old_keys_for_bucket = {
        key for key in context.instance.get_dynamic_partitions(partition_name) if key.startswith(bucket_prefix)
    }

    partitions_to_add = list(new_keys_set - old_keys_for_bucket)
    partitions_to_delete = list(old_keys_for_bucket - new_keys_set)

    truncated_additions = max(len(partitions_to_add) - max_partitions, 0)
    truncated_deletions = max(len(partitions_to_delete) - max_partitions, 0)

    if len(partitions_to_add) > max_partitions:
        partitions_to_add = partitions_to_add[:max_partitions]

    if len(partitions_to_delete) > max_partitions:
        partitions_to_delete = partitions_to_delete[:max_partitions]

    if truncated_additions or truncated_deletions:
        context.log.warning(
            f"Truncated to max_partitions={max_partitions} for bucket '{bucket}': dropped "
            f"{truncated_additions} addition(s) and {truncated_deletions} deletion(s). The partition set "
            f"is incomplete until observed again."
        )
        # The sensor runs in another process and cannot read this run's state, so the fact that the
        # partition set has not converged travels back to it as a run tag.
        context.instance.add_run_tags(context.run_id, PARTITIONS_TRUNCATED_TAG)

    if partitions_to_add:
        context.instance.add_dynamic_partitions(
            partitions_def_name=partition_name,
            partition_keys=partitions_to_add,
        )

    if partitions_to_delete:
        for partition_key in partitions_to_delete:
            context.instance.delete_dynamic_partition(partitions_def_name=partition_name, partition_key=partition_key)

def replace_partition_keys(
    context: OpExecutionContext,
    partition_name: str,
    keys: list[str],
    max_partitions: int,
):
    new_keys_set = set(keys)
    old_partition_keys_set = set(context.instance.get_dynamic_partitions(partition_name))

    partitions_to_add = list(new_keys_set - old_partition_keys_set)
    partitions_to_delete = list(old_partition_keys_set - new_keys_set)

    truncated_additions = max(len(partitions_to_add) - max_partitions, 0)
    truncated_deletions = max(len(partitions_to_delete) - max_partitions, 0)

    if len(partitions_to_add) > max_partitions:
        partitions_to_add = partitions_to_add[:max_partitions]

    if len(partitions_to_delete) > max_partitions:
        partitions_to_delete = partitions_to_delete[:max_partitions]

    if truncated_additions or truncated_deletions:
        context.log.warning(
            f"Truncated to max_partitions={max_partitions}: dropped {truncated_additions} addition(s) "
            f"and {truncated_deletions} deletion(s). The partition set is incomplete until observed again."
        )
        # The sensor runs in another process and cannot read this run's state, so the fact that the
        # partition set has not converged travels back to it as a run tag.
        context.instance.add_run_tags(context.run_id, PARTITIONS_TRUNCATED_TAG)

    if partitions_to_add:
        context.instance.add_dynamic_partitions(
            partitions_def_name=partition_name,
            partition_keys=partitions_to_add,
        )

    if partitions_to_delete:
        for partition_key in partitions_to_delete:
            context.instance.delete_dynamic_partition(partitions_def_name=partition_name, partition_key=partition_key)
