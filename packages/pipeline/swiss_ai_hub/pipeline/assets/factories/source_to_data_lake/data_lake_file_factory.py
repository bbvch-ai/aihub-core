from dagster import AssetIn, AssetKey, AutomationCondition, DynamicPartitionsDefinition, Output, graph_asset

from swiss_ai_hub.pipeline.ops.source.extract_content_from_source_file import extract_content_from_source_file
from swiss_ai_hub.pipeline.ops.source.extract_metadata_from_source_file import extract_metadata_from_source_file
from swiss_ai_hub.pipeline.ops.source.extract_uri_from_source_file import extract_uri_from_source_file
from swiss_ai_hub.pipeline.ops.source.transform_to_data_lake_file import transform_to_data_lake_file
from swiss_ai_hub.pipeline.types.DataLakeFile import DataLakeFile
from swiss_ai_hub.pipeline.types.SourceFile import SourceFile
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def data_lake_file_factory(
    key: AssetKey,
    source_key: str | AssetKey,
    partitions: DynamicPartitionsDefinition,
) -> graph_asset:
    """
    Creates a generic DataLakeFile asset from any source file type.

    This factory creates an asset that takes any SourceFile implementation (SharePoint,
    local file system, etc.) as input, extracts its content and metadata, and transforms
    it into a DataLakeFile. The resulting file is saved to the data lake and provided
    as output for downstream assets.

    This is a generic, reusable factory that works with any source system that implements
    the SourceFile interface, eliminating the need for source-specific transformation logic.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        partitions_def=partitions,
        ins={"source_file": AssetIn(key=source_key)},
        automation_condition=AutomationCondition.eager(),
        description="Creates a DataLakeFile from any SourceFile implementation and saves it to the data lake.",
    )
    def data_lake_file(
        source_file: SourceFile,
    ) -> Output[DataLakeFile]:
        """
        Transform a source file into a data lake file.

        Extracts the source file's URI, metadata, and content, then transforms
        them into a standardized DataLakeFile format suitable for downstream processing.
        """
        uri = extract_uri_from_source_file(source_file=source_file)
        metadata = extract_metadata_from_source_file(source_file=source_file)
        content = extract_content_from_source_file(source_file=source_file)
        return transform_to_data_lake_file(content=content, metadata=metadata, uri=uri)

    return data_lake_file
