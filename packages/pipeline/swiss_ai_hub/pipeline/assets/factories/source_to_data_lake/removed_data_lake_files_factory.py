from dagster import AssetIn, AssetKey, Output, graph_asset

from swiss_ai_hub.pipeline.ops.data_lake.delete_data_lake_files_from_data_lake import (
    delete_data_lake_files_from_data_lake,
)
from swiss_ai_hub.pipeline.ops.source.fetch_data_lake_files_to_remove import fetch_data_lake_files_to_remove
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.source_file import MinimalSourceFile
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def removed_data_lake_files_factory(key: AssetKey, source_key: str | AssetKey) -> graph_asset:
    """
    Creates an asset that removes files from the data lake that no longer exist in the source.

    This generic factory works with any source type (SharePoint, local file system, etc.)
    that implements the MinimalSourceFile interface. It compares files in the source system
    with files in the data lake and removes any data lake files that are no longer present
    in the source.

    This is useful for cleanup operations to ensure the data lake stays in sync with the
    source system and doesn't accumulate orphaned files.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        ins={"source_files": AssetIn(key=source_key)},
        description="Removes documents from the data lake that are no longer present in the source system.",
    )
    def removed_datalake_files(source_files: list[MinimalSourceFile]) -> Output[list[DataLakeFile]]:
        return delete_data_lake_files_from_data_lake(fetch_data_lake_files_to_remove(source_files))

    return removed_datalake_files
