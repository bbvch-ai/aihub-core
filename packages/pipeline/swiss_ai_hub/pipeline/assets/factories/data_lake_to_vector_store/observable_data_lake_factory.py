from dagster import (
    AssetKey,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
    ResourceParam,
    observable_source_asset,
)

from swiss_ai_hub.pipeline.ops.data_lake.data_version_by_partition_for_data_lake import (
    data_version_by_partition_for_data_lake_no_op,
)
from swiss_ai_hub.pipeline.ops.data_lake.fetch_all_files_in_data_lake import fetch_all_files_in_data_lake_no_op
from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def observable_data_lake_factory(
    key: AssetKey,
    partitions: DynamicPartitionsDefinition,
    max_partitions: int,
    encode_partition_keys: bool = True,
) -> observable_source_asset:
    """Route-per-run variant of ``observable_data_lake_factory``.

    The bucket travels in the ``aihub/bucket`` run tag, which the routed ``data_lake_client`` resolves into a
    bucket-scoped ``S3DataLakeClient`` — so ``container_name`` is the run's target bucket. Files are mapped
    onto composite ``{bucket}|{file_uri}`` partition keys reconciled against the shared registry per bucket.
    """

    @observable_source_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        partitions_def=partitions,
        io_manager_key="data_lake_io_manager",
        description="Observes the data lake of each knowledge database this pipeline owns for changes (routed by run tag)",
    )
    def observable_routed_data_lake(
        context: OpExecutionContext,
        data_lake_client: ResourceParam[S3DataLakeClient],
    ) -> DataVersionsByPartition:
        bucket = data_lake_client.container_name
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

    return observable_routed_data_lake
