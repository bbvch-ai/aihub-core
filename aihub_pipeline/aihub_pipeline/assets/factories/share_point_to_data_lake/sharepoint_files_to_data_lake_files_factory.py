from dagster import AssetIn, AssetKey, AutomationCondition, DynamicPartitionsDefinition, Output, graph_asset

from aihub_pipeline.ops.share_point.extract_content_from_share_point_file import extract_content_from_share_point_file
from aihub_pipeline.ops.share_point.extract_metadata_from_share_point_file import extract_metadata_from_share_point_file
from aihub_pipeline.ops.share_point.extract_uri_from_share_point_file import extract_uri_from_share_point_file
from aihub_pipeline.ops.share_point.transform_to_data_lake_file import transform_to_data_lake_file
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.SharePointFile import SharePointFile
from aihub_pipeline.util.key_utils import group_name_from_asset_key


def share_point_files_to_data_lake_files_factory(
    key: AssetKey,
    share_point_key: str | AssetKey,
    partitions: DynamicPartitionsDefinition,
) -> graph_asset:
    """
    Creates a DataLakeFile asset. This asset takes a SharePoint file as input, parses it into a DataLakeFile, and saves
    it into the DataLake, as well as providing it as an output for downstream assets.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        partitions_def=partitions,
        ins={"share_point_file": AssetIn(key=share_point_key)},
        automation_condition=AutomationCondition.eager(),
        description="Creates a DataLakeFile from a SharePointFile and saves it to the data lake.",
    )
    def data_lake_file(
        share_point_file: SharePointFile,
    ) -> Output[DataLakeFile]:
        uri = extract_uri_from_share_point_file(share_point_file=share_point_file)
        metadata = extract_metadata_from_share_point_file(share_point_file=share_point_file)
        content = extract_content_from_share_point_file(share_point_file=share_point_file)
        return transform_to_data_lake_file(content=content, metadata=metadata, uri=uri)

    return data_lake_file
