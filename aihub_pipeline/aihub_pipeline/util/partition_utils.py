from dagster import OpExecutionContext


def replace_partition_keys(context: OpExecutionContext, partition_name: str, keys: list[str]):
    new_keys_set = set(keys)
    old_partition_keys_set = set(context.instance.get_dynamic_partitions(partition_name))

    partitions_to_add = list(new_keys_set - old_partition_keys_set)
    partitions_to_delete = list(old_partition_keys_set - new_keys_set)

    if partitions_to_add:
        context.instance.add_dynamic_partitions(
            partitions_def_name=partition_name,
            partition_keys=partitions_to_add,
        )

    if partitions_to_delete:
        for partition_key in partitions_to_delete:
            context.instance.delete_dynamic_partition(partitions_def_name=partition_name, partition_key=partition_key)
