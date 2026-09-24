from dagster import AssetIn, AssetKey, Output, graph_asset

from swiss_ai_hub.pipeline.ops.source.routed.announce_removed_files import announce_removed_files
from swiss_ai_hub.pipeline.ops.source.routed.delete_data_lake_files_from_bucket import (
    delete_data_lake_files_from_bucket,
)
from swiss_ai_hub.pipeline.ops.source.routed.fetch_bucket_files_to_remove import fetch_bucket_files_to_remove
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.source_file import MinimalSourceFile
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def routed_removed_data_lake_files_factory(key: AssetKey, source_key: str | AssetKey) -> graph_asset:
    """Removes from this run's database whatever its source no longer has, then announces each removal."""

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        ins={"source_files": AssetIn(key=source_key)},
        description="Removes data lake files the source no longer has and notifies the ingestion pipeline.",
    )
    def routed_removed_data_lake_files(source_files: list[MinimalSourceFile]) -> Output[list[DataLakeFile]]:
        return announce_removed_files(delete_data_lake_files_from_bucket(fetch_bucket_files_to_remove(source_files)))

    return routed_removed_data_lake_files
