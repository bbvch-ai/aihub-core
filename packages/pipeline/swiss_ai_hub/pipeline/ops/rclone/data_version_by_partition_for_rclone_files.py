from dagster import (
    AssetKey,
    AssetMaterialization,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
)

from swiss_ai_hub.pipeline.types.rclone_file import MinimalRcloneFile
from swiss_ai_hub.pipeline.util.meta_utils import rclone_file_metadata_table
from swiss_ai_hub.pipeline.util.partition_utils import make_composite_partition_key, replace_partition_keys_for_bucket


def data_version_by_partition_for_rclone_files(
    context: OpExecutionContext,
    asset_key: AssetKey,
    partition: DynamicPartitionsDefinition,
    bucket: str,
    rclone_files: list[MinimalRcloneFile],
    max_partitions: int,
) -> DataVersionsByPartition:
    """
    Maps one database's remote files onto composite ``{bucket}|{path}`` partitions and versions them.

    The registry is shared by every database the pipeline fills, so reconciliation is scoped to this bucket's
    prefix: one database's observation can never delete another's partitions. Files directly at the root of the
    remote are skipped, because the ingestion pipeline maps the first path segment to a namespace and never
    ingests a root-level object; counting them in the metadata makes the omission visible.

    Versions prefer the backend's content hash (any change, no false positives) and fall back to mtime+size.
    """
    nested_files = [file for file in rclone_files if "/" in file.path.strip("/")]
    skipped_root_files = len(rclone_files) - len(nested_files)
    key_by_path = {file.path: make_composite_partition_key(bucket, file.path) for file in nested_files}

    replace_partition_keys_for_bucket(context, partition.name, bucket, list(key_by_path.values()), max_partitions)

    context.log.info(f"Found {len(nested_files)} file(s) for '{bucket}', skipped {skipped_root_files} at the root")
    if skipped_root_files:
        context.log.warning(
            f"{skipped_root_files} file(s) lie directly at the root of the source of '{bucket}' and are not synced: "
            "only files inside a top-level folder (which becomes a namespace) are ingested."
        )

    if nested_files:
        last_file = sorted(nested_files, key=lambda file: file.path)[-1]
        context.instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=asset_key,
                partition=key_by_path[last_file.path],
                metadata={
                    "Bucket": bucket,
                    "Number of Files": len(nested_files),
                    "Skipped root-level files": skipped_root_files,
                    "Total File Size (MB)": sum(file.size for file in nested_files) / 1e6,
                    "Table": rclone_file_metadata_table(nested_files),
                },
            )
        )

    def data_version(file: MinimalRcloneFile) -> str:
        if file.hashes:
            hash_value = file.hashes.get("md5") or file.hashes.get("sha1") or next(iter(file.hashes.values()))
            return f"hash:{hash_value}"
        return f"mtime:{file.modified}-{file.size}"

    existing = set(context.instance.get_dynamic_partitions(partition.name))
    return DataVersionsByPartition(
        {key_by_path[file.path]: data_version(file) for file in nested_files if key_by_path[file.path] in existing}
    )
