from dagster import OpExecutionContext

PARTITIONS_TRUNCATED_TAG = {"partitions-truncated": "true"}


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
