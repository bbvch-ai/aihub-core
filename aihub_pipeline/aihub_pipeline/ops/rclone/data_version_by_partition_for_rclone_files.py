from dagster import (
    AssetKey,
    AssetMaterialization,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
)

from aihub_pipeline.types.RcloneFile import MinimalRcloneFile
from aihub_pipeline.util.meta_utils import rclone_file_metadata_table
from aihub_pipeline.util.partition_utils import replace_partition_keys


def data_version_by_partition_for_rclone_files(
    context: OpExecutionContext,
    asset_key: AssetKey,
    partition: DynamicPartitionsDefinition,
    rclone_files: list[MinimalRcloneFile],
) -> DataVersionsByPartition:
    """
    Generates a dynamic partition key for each file from the rclone remote,
    reports the materialization and returns a DataVersion for each partition key.

    **Change Detection Strategy**:
    - Primary: Content hash (MD5/SHA1) from backend if available (Dropbox, OneDrive, S3, etc.)
    - Fallback: mtime + size for backends without hash support

    Hash-based detection is superior: detects ANY content change with zero false positives.
    """
    partition_keys = [file.path for file in rclone_files]

    replace_partition_keys(
        context,
        partition.name,
        partition_keys,
    )

    context.log.info(f"Found {len(rclone_files)} files in rclone remote")
    context.log.info("Materializing external rclone source asset")

    if len(rclone_files) > 0:
        # Sort files by path to ensure deterministic partition selection for materialization
        sorted_files = sorted(rclone_files, key=lambda f: f.path)
        context.instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=asset_key,
                partition=sorted_files[-1].path,
                metadata={
                    "Number of Files": len(rclone_files),
                    "Total File Size (MB)": sum([file.size for file in rclone_files]) / 1e6,
                    "Table": rclone_file_metadata_table(rclone_files),
                },
            )
        )

    # Use hash checksum if available (content-based), otherwise fallback to mtime+size
    # Hash is superior: detects ANY content change, no false positives
    # Fallback ensures it works even if backend doesn't support hashes
    def get_data_version(file: MinimalRcloneFile) -> str:
        if file.hashes:
            # Prefer MD5 (widely supported), fallback to any available hash
            hash_value = file.hashes.get("md5") or file.hashes.get("sha1") or next(iter(file.hashes.values()))
            return f"hash:{hash_value}"
        # Fallback to mtime+size if no hash available
        return f"mtime:{file.modified}-{file.size}"

    return DataVersionsByPartition({file.path: get_data_version(file) for file in rclone_files})
