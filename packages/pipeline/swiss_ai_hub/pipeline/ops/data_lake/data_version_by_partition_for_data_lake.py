from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    MetadataValue,
    OpExecutionContext,
)

from swiss_ai_hub.pipeline.types.data_lake_listing import DataLakeListing
from swiss_ai_hub.pipeline.util.meta_utils import data_lake_metadata_table
from swiss_ai_hub.pipeline.util.partition_utils import make_composite_partition_key, replace_partition_keys_for_bucket

SKIPPED_COUNT_METADATA_KEY = "Skipped files (namespace collision)"
SKIPPED_TABLE_METADATA_KEY = "Skipped files"


def data_version_by_partition_for_data_lake_no_op(
    context: OpExecutionContext,
    asset_key: AssetKey,
    partition: DynamicPartitionsDefinition,
    bucket: str,
    listing: DataLakeListing,
    max_partitions: int,
    encode_partition_keys: bool = True,
) -> DataVersionsByPartition:
    """Route-per-run variant of ``data_version_by_partition_for_data_lake_files_no_op``.

    The document ingestion pipeline shares one partition registry across all knowledge databases, so partition keys
    are composite ``{bucket}|{file_uri}`` and reconciliation is scoped to the run's bucket via
    ``replace_partition_keys_for_bucket`` — one bucket's observe run can never delete another's partitions.

    Files the listing skipped get no partition, so they are never ingested; the metadata and a warning name them,
    because a skipped folder is otherwise indistinguishable from an empty one.
    """
    data_lake_files = listing.files
    key_by_uri = {
        file.uri: make_composite_partition_key(bucket, file.uri, encode=encode_partition_keys)
        for file in data_lake_files
    }
    partition_keys = list(key_by_uri.values())

    replace_partition_keys_for_bucket(
        context,
        partition.name,
        bucket,
        partition_keys,
        max_partitions=max_partitions,
    )
    context.log.info(
        f"Found {len(data_lake_files)} files in the data lake for bucket '{bucket}', skipped {len(listing.skipped)}"
    )
    for reason in sorted({skipped_file.reason for skipped_file in listing.skipped}):
        context.log.warning(f"Not ingested in '{bucket}': {reason}")
    _report_listing(context, asset_key, bucket, listing, key_by_uri)

    existing_partitions = set(context.instance.get_dynamic_partitions(partition.name))
    files_with_partitions = [
        data_lake_file for data_lake_file in data_lake_files if key_by_uri[data_lake_file.uri] in existing_partitions
    ]

    return DataVersionsByPartition(
        {
            key_by_uri[data_lake_file.uri]: f"{data_lake_file.updated}-{data_lake_file.hash}"
            for data_lake_file in files_with_partitions
        }
    )


def _report_listing(
    context: OpExecutionContext,
    asset_key: AssetKey,
    bucket: str,
    listing: DataLakeListing,
    key_by_uri: dict[str, str],
) -> None:
    """A skipped file has no partition to attach an event to, so when every file was skipped the report goes out as
    an unpartitioned observation: without a data version it changes no partition and triggers no ingestion."""
    if not listing.files and not listing.skipped:
        return
    metadata = {
        "Bucket": bucket,
        "Number of Files": len(listing.files),
        "Total File Size (MB)": sum(data_lake_file.size for data_lake_file in listing.files) / 1e6,
        "Table": data_lake_metadata_table(listing.files),
        SKIPPED_COUNT_METADATA_KEY: len(listing.skipped),
    }
    if listing.skipped:
        metadata[SKIPPED_TABLE_METADATA_KEY] = MetadataValue.md(listing.skipped_as_markdown())
    if listing.files:
        event = AssetMaterialization(
            asset_key=asset_key, partition=key_by_uri[listing.files[-1].uri], metadata=metadata
        )
    else:
        event = AssetObservation(asset_key=asset_key, metadata=metadata)
    context.instance.report_runless_asset_event(event)
