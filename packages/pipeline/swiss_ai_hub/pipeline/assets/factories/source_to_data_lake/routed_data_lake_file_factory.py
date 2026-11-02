from dagster import AssetIn, AssetKey, AutomationCondition, DynamicPartitionsDefinition, Output, graph_asset

from swiss_ai_hub.pipeline.ops.source.extract_content_from_source_file import extract_content_from_source_file
from swiss_ai_hub.pipeline.ops.source.extract_metadata_from_source_file import extract_metadata_from_source_file
from swiss_ai_hub.pipeline.ops.source.routed.build_data_lake_uri_for_bucket import build_data_lake_uri_for_bucket
from swiss_ai_hub.pipeline.ops.source.routed.write_data_lake_file_to_bucket import write_data_lake_file_to_bucket
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.source_file import SourceFile
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def routed_data_lake_file_factory(
    key: AssetKey,
    source_key: str | AssetKey,
    partitions: DynamicPartitionsDefinition,
) -> graph_asset:
    """Lands one source file in the data lake of the database its partition key names and announces it.

    Same shape as ``data_lake_file_factory`` up to the last step, which writes and announces in one op instead of
    leaving the write to an IO manager: the announcement has to follow the write.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        partitions_def=partitions,
        ins={"source_file": AssetIn(key=source_key)},
        automation_condition=AutomationCondition.eager(),
        description="Writes a source file into its knowledge database's data lake and notifies the ingestion pipeline.",
    )
    def routed_data_lake_file(source_file: SourceFile) -> Output[DataLakeFile]:
        uri = build_data_lake_uri_for_bucket(source_file=source_file)
        metadata = extract_metadata_from_source_file(source_file=source_file)
        content = extract_content_from_source_file(source_file=source_file)
        return write_data_lake_file_to_bucket(content=content, metadata=metadata, uri=uri)

    return routed_data_lake_file
