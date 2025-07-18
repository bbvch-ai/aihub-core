from dagster import AssetIn, AssetKey, AutomationCondition, Output, graph_asset

from aihub_pipeline.ops.share_point.delete_data_lake_files_from_data_lake import delete_data_lake_files_from_data_lake
from aihub_pipeline.ops.share_point.fetch_data_lake_files_to_remove import fetch_data_lake_files_to_remove
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.SharePointFile import MinimalSharePointFile
from aihub_pipeline.util.key_utils import group_name_from_asset_key


def removed_data_lake_files_factory(key: AssetKey, share_point_key: str | AssetKey) -> graph_asset:
    """
    Pseudo-Asset that removes SharePoint files from the data lake that are no longer present
    in the SharePoint.
    This asset takes a list of SharePointFiles as input, compares the documents in the SharePoint to the documents
    in the Data Lake, and removes any documents that are no longer present in SharePoint from the Data Lake.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        ins={"share_point_files": AssetIn(key=share_point_key)},
        automation_condition=AutomationCondition.eager(),
        description="Removes documents from the Data Lake that are no longer present in SharePoint.",
    )
    def removed_datalake_files(share_point_files: list[MinimalSharePointFile]) -> Output[list[DataLakeFile]]:
        return delete_data_lake_files_from_data_lake(fetch_data_lake_files_to_remove(share_point_files))

    return removed_datalake_files
