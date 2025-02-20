from typing import List

from dagster import OpExecutionContext


def replace_partition_keys(context: OpExecutionContext, partition_name: str, keys: List[str]):
    old_partition_keys = context.instance.get_dynamic_partitions(partition_name)
    for old_partition_key in old_partition_keys:
        context.instance.delete_dynamic_partition(partitions_def_name=partition_name, partition_key=old_partition_key)
    context.instance.add_dynamic_partitions(
        partitions_def_name=partition_name,
        partition_keys=keys,
    )
