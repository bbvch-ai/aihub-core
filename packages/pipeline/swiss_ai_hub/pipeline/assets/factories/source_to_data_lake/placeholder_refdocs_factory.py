from dagster import AssetIn, AssetKey, AutomationCondition, DynamicPartitionsDefinition, Output, graph_asset

from swiss_ai_hub.pipeline.ops.document.create_placeholder_refdoc import create_placeholder_refdoc_from_data_lake_file
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def placeholder_refdocs_factory(
    key: AssetKey,
    data_lake_files_key: AssetKey,
    partitions: DynamicPartitionsDefinition,
) -> graph_asset:
    """
    Creates placeholder RefDoc entries after files are successfully written to the data lake.

    This factory creates an asset that depends on the data_lake_files asset and creates
    placeholder RefDocDocument entries with 'pending' status. This enables immediate visibility
    of uploaded files in the UI while they await full processing.

    The RefDoc is only created AFTER the S3 write succeeds, ensuring data consistency.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        partitions_def=partitions,
        ins={"data_lake_file": AssetIn(key=data_lake_files_key)},
        automation_condition=AutomationCondition.eager(),
        description="Creates placeholder RefDoc entries for tracking pipeline-uploaded files.",
    )
    def placeholder_refdocs(
        data_lake_file: DataLakeFile,
    ) -> Output[RefDocDocument]:
        return create_placeholder_refdoc_from_data_lake_file(data_lake_file)

    return placeholder_refdocs
