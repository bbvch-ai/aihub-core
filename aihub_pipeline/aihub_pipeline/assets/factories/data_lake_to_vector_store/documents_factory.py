from dagster import AssetIn, AssetKey, AutomationCondition, DynamicPartitionsDefinition, Output, graph_asset

from aihub_pipeline.ops.data_lake.generate_figure_descriptions import generate_figure_descriptions
from aihub_pipeline.ops.data_lake.parse_document_from_data_lake import parse_document_from_data_lake
from aihub_pipeline.ops.document.ensure_refdoc_default_metadata import ensure_refdoc_default_metadata
from aihub_pipeline.ops.document.insert_ref_doc_into_docstore import insert_ref_doc_into_docstore
from aihub_pipeline.ops.document.refine_document_text import refine_document_text
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.RefDocDocument import RefDocDocument
from aihub_pipeline.util.key_utils import group_name_from_asset_key


def documents_factory(
    key: AssetKey,
    data_lake_key: str | AssetKey,
    partitions: DynamicPartitionsDefinition,
    enable_text_refinement: bool = False,
) -> graph_asset:
    """
    Creates a document asset that represents a Ref Doc in the Document Store.
    This asset takes a Data Lake File as input, parses it into a Ref Doc, and saves the corresponding
    Ref Doc with the text and image url into the Document store, as well as providing it as an output for
    downstream assets.

    When enable_text_refinement is True, the TextRefinementResource must be provided in the resources.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        ins={"data_lake_file": AssetIn(key=data_lake_key)},
        partitions_def=partitions,
        automation_condition=AutomationCondition.eager(),
        description="Create RefDocs from data lake files and insert them into the docstore",
    )
    def document(
        data_lake_file: DataLakeFile,
    ) -> Output[RefDocDocument]:
        parsed = parse_document_from_data_lake(data_lake_file)
        with_figures = generate_figure_descriptions(parsed)

        if enable_text_refinement:
            refined = refine_document_text(with_figures)
            validated = ensure_refdoc_default_metadata(refined)
        else:
            validated = ensure_refdoc_default_metadata(with_figures)

        return insert_ref_doc_into_docstore(validated)

    return document
