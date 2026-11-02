from dagster import OpExecutionContext, Output, op
from llama_index.core.schema import TextNode

from swiss_ai_hub.pipeline.resources.parser.markdown_structural_node_parser_resource import (
    MarkdownStructuralNodeParserResource,
)
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_partition_key


@op(code_version="v1")
def chunk_ref_doc_into_nodes(
    context: OpExecutionContext,
    ref_doc: RefDocDocument,
    node_parser: MarkdownStructuralNodeParserResource,
) -> Output[list[TextNode]]:
    """Route-per-run variant of ``chunk_ref_doc_into_nodes_using_md_structural_node_parser``.

    Resolves the document store name from the composite partition key's bucket instead of from a fixed
    ``doc_store_resource``, so one deployed pipeline chunks documents for every self-service database.
    """
    bucket = bucket_from_partition_key(context.partition_key)
    store_name = get_db_name_from_bucket_name(bucket)
    parser = node_parser.get_node_parser_for_ref_doc(ref_doc=ref_doc, document_store_name=store_name, bucket=bucket)
    nodes = parser.get_nodes_from_documents([ref_doc])
    context.log.info(f"Successfully chunked {len(nodes)} nodes from ref_doc {ref_doc.id_}")
    return Output(nodes)
