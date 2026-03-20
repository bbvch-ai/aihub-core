from dagster import OpExecutionContext, Output, op
from llama_index.core.schema import TextNode

from swiss_ai_hub.pipeline.resources.doc_store.doc_store_resource import DocStoreResource
from swiss_ai_hub.pipeline.resources.parser.markdown_structural_node_parser_resource import (
    MarkdownStructuralNodeParserResource,
)
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument


@op(code_version="v1")
def chunk_ref_doc_into_nodes_using_md_structural_node_parser(
    context: OpExecutionContext,
    ref_doc: RefDocDocument,
    node_parser: MarkdownStructuralNodeParserResource,
    doc_store_resource: DocStoreResource,
) -> Output[list[TextNode]]:
    """Uses the node parser resource to chunk the ref doc into nodes."""
    node_parser = node_parser.get_node_parser_for_ref_doc(
        ref_doc=ref_doc, document_store_name=doc_store_resource.document_store_name
    )
    nodes = node_parser.get_nodes_from_documents([ref_doc])
    context.log.info(f"Successfully chunked {len(nodes)} nodes from ref_doc {ref_doc.id_}")
    return Output(nodes)
