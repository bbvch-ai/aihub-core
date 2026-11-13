from dagster import AssetIn, AssetKey, AutomationCondition, DynamicPartitionsDefinition, Output, graph_asset

from swiss_ai_hub.pipeline.ops.data_lake.generate_figure_descriptions import generate_figure_descriptions
from swiss_ai_hub.pipeline.ops.data_lake.parse_document_from_data_lake import parse_document_from_data_lake
from swiss_ai_hub.pipeline.ops.document.apply_markdown_frontmatter import apply_markdown_frontmatter
from swiss_ai_hub.pipeline.ops.document.classify_document import classify_document
from swiss_ai_hub.pipeline.ops.document.ensure_refdoc_default_metadata import ensure_refdoc_default_metadata
from swiss_ai_hub.pipeline.ops.document.insert_ref_doc_into_docstore import insert_ref_doc_into_docstore
from swiss_ai_hub.pipeline.ops.document.refine_document_tables import refine_document_tables
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def documents_factory(
    key: AssetKey,
    data_lake_key: str | AssetKey,
    partitions: DynamicPartitionsDefinition,
) -> graph_asset:
    """
    Creates a document asset that represents a Ref Doc in the Document Store.
    This asset takes a Data Lake File as input, parses it into a Ref Doc, and saves the corresponding
    Ref Doc with the text and image url into the Document store, as well as providing it as an output for
    downstream assets.

    Figure descriptions, table refinement and document classification are always part of the graph; each op decides
    per run, from the knowledge database in the partition key, whether it has work to do. A markdown file's frontmatter
    is applied right after parsing, so no later op, and in particular no LLM, is handed the YAML. Classification reads
    the refined text, so a total it reads from a table is read from the refined table.
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
        fronted = apply_markdown_frontmatter(parsed)
        described = generate_figure_descriptions(fronted)
        refined = refine_document_tables(described)
        classified = classify_document(refined)
        validated = ensure_refdoc_default_metadata(classified)

        return insert_ref_doc_into_docstore(validated)

    return document
