from dagster import AssetIn, AssetKey, AutomationCondition, DynamicPartitionsDefinition, Output, graph_asset

from aihub_pipeline.ops.data_lake.generate_figure_descriptions import generate_figure_descriptions
from aihub_pipeline.ops.data_lake.parse_document_from_data_lake import parse_document_from_data_lake
from aihub_pipeline.ops.document.ensure_refdoc_default_metadata import ensure_refdoc_default_metadata
from aihub_pipeline.ops.document.insert_ref_doc_into_docstore import insert_ref_doc_into_docstore
from aihub_pipeline.ops.document.refine_document_tables import refine_document_tables
from aihub_pipeline.ops.document.refine_document_text import refine_document_text
from aihub_pipeline.ops.document.validate_and_reparse_document import validate_and_reparse_document
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.RefDocDocument import RefDocDocument
from aihub_pipeline.util.key_utils import group_name_from_asset_key


def documents_factory(
    key: AssetKey,
    data_lake_key: str | AssetKey,
    partitions: DynamicPartitionsDefinition,
    enable_text_refinement: bool = False,
    enable_table_refinement: bool = False,
    enable_quality_validation: bool = True,
) -> graph_asset:
    """
    Creates a document asset that represents a Ref Doc in the Document Store.
    This asset takes a Data Lake File as input, parses it into a Ref Doc, and saves the corresponding
    Ref Doc with the text and image url into the Document store, as well as providing it as an output for
    downstream assets.

    When enable_quality_validation is True (default), validates parsed documents for severe parsing bugs
    (like excessive text repetition) and re-parses if needed. This catches Docling parsing failures.
    When enable_text_refinement is True, the TextRefinementResource must be provided in the resources.
    When enable_table_refinement is True, the TableRefinementResource must be provided in the resources.
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

        # Validate for severe parsing bugs and re-parse if needed
        if enable_quality_validation:
            parsed = validate_and_reparse_document(parsed, data_lake_file)

        with_figures = generate_figure_descriptions(parsed)

        current = with_figures

        if enable_table_refinement:
            current = refine_document_tables(current)

        if enable_text_refinement:
            current = refine_document_text(current)

        validated = ensure_refdoc_default_metadata(current)

        return insert_ref_doc_into_docstore(validated)

    return document
