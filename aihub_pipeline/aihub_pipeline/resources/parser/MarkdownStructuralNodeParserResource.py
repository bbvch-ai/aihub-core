from aihub_lib.generative_ai.document.parsers.MarkdownStructuralNodeParser import MarkdownStructuralNodeParser
from dagster import ConfigurableResource
from llama_index.core.node_parser import NodeParser

from aihub_pipeline.types.RefDocDocument import RefDocDocument


class MarkdownStructuralNodeParserResource(ConfigurableResource):
    """
    This resource specifies the NodeParser to use to split a RefDoc into a set of TextNodes
    using the MarkdownStructuralNodeParser.

    Example usage:

    1. Split a RefDoc into a set of nodes:

    .. code-block:: python
        from aihub_pipeline.resources.app.MarkdownStructuralNodeParserResource import MarkdownStructuralNodeParserResource

        from dagster import Definitions, asset

        @asset
        def asset1(
            ref_doc: RefDocDocument,
            node_parser_resource: NodeParserResource,
        ):
            node_parser = node_parser_resource.get_node_parser_for_ref_doc(ref_doc)
            nodes = node_parser.get_nodes_from_documents([ref_doc])
            ...

        defs = Definitions(
            assets=[asset1],
            resources={
                "node_parser": MarkdownStructuralNodeParserResource(),
            },
        )
    """

    def get_node_parser_for_ref_doc(self, ref_doc: RefDocDocument) -> NodeParser:
        return MarkdownStructuralNodeParser(metadata=ref_doc.metadata)
