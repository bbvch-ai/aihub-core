from dagster import AssetIn, AssetKey, Output, graph_asset

from aihub_pipeline.ops.data_lake.delete_data_lake_files_from_data_lake import delete_data_lake_files_from_data_lake
from aihub_pipeline.ops.source.fetch_data_lake_files_to_remove import fetch_data_lake_files_to_remove
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.SourceFile import MinimalSourceFile
from aihub_pipeline.util.key_utils import group_name_from_asset_key


def removed_data_lake_files_factory(key: AssetKey, source_key: str | AssetKey) -> graph_asset:
    """
    Creates an asset that removes files from the data lake that no longer exist in the source.

    This generic factory works with any source type (SharePoint, local file system, etc.)
    that implements the MinimalSourceFile interface. It compares files in the source system
    with files in the data lake and removes any data lake files that are no longer present
    in the source.

    This is useful for cleanup operations to ensure the data lake stays in sync with the
    source system and doesn't accumulate orphaned files.

    Args:
        key: The asset key for the removed files tracking asset.
        source_key: The asset key of the upstream source files (e.g., SharePoint, file system).

    Returns:
        A graph_asset that identifies and removes orphaned data lake files.

    Example:
        ```python
        # Remove orphaned files from SharePoint sync
        removed_sharepoint_files = removed_data_lake_files_factory(
            key=AssetKey(["removed_data_lake_files"]),
            source_key=AssetKey(["sharepoint_files"]),
        )

        # Remove orphaned files from file system sync
        removed_filesystem_files = removed_data_lake_files_factory(
            key=AssetKey(["removed_data_lake_files"]),
            source_key=AssetKey(["filesystem_files"]),
        )
        ```
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        ins={"source_files": AssetIn(key=source_key)},
        description="Removes documents from the data lake that are no longer present in the source system.",
    )
    def removed_datalake_files(source_files: list[MinimalSourceFile]) -> Output[list[DataLakeFile]]:
        """
        Identify and remove orphaned data lake files.

        Compares source files with data lake files and removes any files
        that exist in the data lake but not in the source system.
        """
        return delete_data_lake_files_from_data_lake(fetch_data_lake_files_to_remove(source_files))

    return removed_datalake_files
