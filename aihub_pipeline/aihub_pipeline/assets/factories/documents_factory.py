from dagster import (
    AssetIn,
    AssetKey,
    AutomationCondition,
    DynamicPartitionsDefinition,
    Output,
    graph_asset,
)

from aihub_pipeline.ops.data_lake.doc_with_figures_to_ref_doc import doc_with_figures_to_ref_doc
from aihub_pipeline.ops.data_lake.inject_figures import inject_figures
from aihub_pipeline.ops.data_lake.parse_document_from_data_lake import parse_document_from_data_lake
from aihub_pipeline.ops.data_lake.reformat_tables import reformat_tables
from aihub_pipeline.ops.data_lake.save_figures_to_data_lake import save_figures_to_data_lake
from aihub_pipeline.ops.document.ensure_refdoc_default_metadata import ensure_refdoc_default_metadata
from aihub_pipeline.ops.document.insert_ref_doc_into_docstore import insert_ref_doc_into_docstore
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.RefDocDocument import RefDocDocument
from aihub_pipeline.util.key_utils import group_name_from_asset_key


def documents_factory(
    key: AssetKey, data_lake_key: str | AssetKey, partitions: DynamicPartitionsDefinition
) -> graph_asset:
    """
    Creates a document asset that represents a Ref Doc in the Document Store.
    This asset takes a Data Lake File as input, parses it into a Ref Doc, and saves the corresponding
    Ref Doc with the text and image content into the Document store, as well as providing it as an output for
    downstream assets.
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
        doc_with_figures = parse_document_from_data_lake(data_lake_file)
        figure_metadata = save_figures_to_data_lake(doc_with_figures, data_lake_file)
        doc_with_figures = inject_figures(doc_with_figures, figure_metadata)
        doc_with_figures = reformat_tables(doc_with_figures)

        return insert_ref_doc_into_docstore(ensure_refdoc_default_metadata(doc_with_figures_to_ref_doc(data_lake_file, doc_with_figures)))

    return document
