from typing import List

from dagster import OpExecutionContext, op
from llama_index.core.schema import TextNode

from pipelines_core.resources.parser.MarkdownStructuralNodeParserResource import (
    MarkdownStructuralNodeParserResource,
)
from pipelines_core.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def chunk_ref_doc_into_nodes_using_md_structural_node_parser(
    context: OpExecutionContext,
    ref_doc: RefDocDocument,
    node_parser: MarkdownStructuralNodeParserResource,
) -> List[TextNode]:
    """Uses the node parser resource to chunk the ref doc into nodes."""
    node_parser = node_parser.get_node_parser_for_ref_doc(ref_doc)
    nodes = node_parser.get_nodes_from_documents([ref_doc])
    context.log.info(
        f"Successfully chunked {len(nodes)} nodes from ref_doc {ref_doc.id_}"
    )
    return nodes
