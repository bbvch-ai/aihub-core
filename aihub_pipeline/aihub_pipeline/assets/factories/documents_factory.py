from dagster import AssetIn, AssetKey, AutomationCondition, DynamicPartitionsDefinition, Output, graph_asset

from aihub_pipeline.ops.data_lake.data_lake_file_to_ref_doc import data_lake_file_to_ref_doc
from aihub_pipeline.ops.document.describe_images import describe_images
from aihub_pipeline.ops.document.extract_images import extract_images
from aihub_pipeline.ops.document.inject_figures import inject_figures
from aihub_pipeline.ops.document.insert_ref_doc_into_docstore import insert_ref_doc_into_docstore
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.RefDocDocument import RefDocDocument
from aihub_pipeline.util.key_utils import group_name_from_asset_key


def documents_factory(
    key: AssetKey, data_lake_key: str | AssetKey, partitions: DynamicPartitionsDefinition
) -> graph_asset:
    """Creates a document asset that represents a Ref Doc in the Document Store.
    This asset takes a Data Lake File as input, parses it into a Ref Doc, extracts and processes images,
    and saves the corresponding Ref Doc with the text content and image information into the Document store,
    as well as providing it as an output for downstream assets.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        ins={"data_lake_file": AssetIn(key=data_lake_key)},
        partitions_def=partitions,
        automation_condition=AutomationCondition.eager(),
        description="Create RefDocs from data lake files and insert them into the docstore",
    )
    def document(data_lake_file: DataLakeFile) -> Output[RefDocDocument]:
        ref_doc = data_lake_file_to_ref_doc(data_lake_file)
        ref_doc_with_images = extract_images(ref_doc)
        images_with_descriptions = describe_images(ref_doc_with_images)
        final_ref_doc = inject_figures(images_with_descriptions)
        return insert_ref_doc_into_docstore(final_ref_doc)

    return document
