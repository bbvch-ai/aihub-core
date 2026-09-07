from dagster import (
    AssetKey,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
    observable_source_asset,
)

from swiss_ai_hub.pipeline.ops.data_lake.data_version_by_partition_for_data_lake import (
    data_version_by_partition_for_data_lake_no_op,
)
from swiss_ai_hub.pipeline.ops.data_lake.fetch_all_files_in_data_lake import fetch_all_files_in_data_lake_no_op
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client


def observable_data_lake_factory(
    key: AssetKey,
    partitions: DynamicPartitionsDefinition,
    max_partitions: int,
    encode_partition_keys: bool = True,
) -> observable_source_asset:
    """Observes one knowledge database's data lake, resolved from the run.

    The bucket travels in the ``aihub/bucket`` run tag. Files are mapped onto composite
    ``{bucket}|{file_uri}`` partition keys, reconciled against the shared registry per bucket so one
    database's observation never touches another's partitions.

    The client is built here rather than injected: it is provisioned with ``ensure_bucket=True`` because
    this is the first thing to touch a freshly created database's bucket.
    """

    @observable_source_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        partitions_def=partitions,
        io_manager_key="data_lake_io_manager",
        description="Observes the data lake of the knowledge database this run targets (routed by run tag)",
    )
    def observable_data_lake(context: OpExecutionContext) -> DataVersionsByPartition:
        bucket = bucket_from_run_tag(context)
        data_lake_client = build_s3_data_lake_client(bucket, ensure_bucket=True)
        data_lake_files: list[DataLakeFile] = fetch_all_files_in_data_lake_no_op(data_lake_client=data_lake_client)
        return data_version_by_partition_for_data_lake_no_op(
            context=context,
            asset_key=key,
            partition=partitions,
            bucket=bucket,
            data_lake_files=data_lake_files,
            max_partitions=max_partitions,
            encode_partition_keys=encode_partition_keys,
        )

    return observable_data_lake
