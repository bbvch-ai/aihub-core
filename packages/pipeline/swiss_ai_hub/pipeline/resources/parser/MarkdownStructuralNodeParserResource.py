from dagster import ConfigurableResource, ResourceDependency
from swiss_ai_hub.core.generative_ai.document.parsers.MarkdownStructuralNodeParser import MarkdownStructuralNodeParser
from swiss_ai_hub.core.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_STORE_NAME

from swiss_ai_hub.pipeline.types.RefDocDocument import RefDocDocument


class MarkdownStructuralNodeParserResource(ConfigurableResource):
    """
    This resource specifies the NodeParser to use to split a RefDoc into a set of TextNodes
    using the MarkdownStructuralNodeParser.

    Example usage:

    1. Split a RefDoc into a set of nodes:

    ... code-block:: python
        from swiss_ai_hub.pipeline.resources.app.MarkdownStructuralNodeParserResource import MarkdownStructuralNodeParserResource

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
                "node_parser": MarkdownStructuralNodeParserResource(
                    llm_config=my_llm_config
                ),
            }
        )
    """  # noqa: E501

    llm_config: ResourceDependency[LLMConfig]

    def get_node_parser_for_ref_doc(
        self, ref_doc: RefDocDocument, document_store_name: str
    ) -> MarkdownStructuralNodeParser:
        metadata = ref_doc.metadata
        metadata[DOCUMENT_STORE_NAME] = document_store_name
        return MarkdownStructuralNodeParser(metadata=metadata, llm_config=self.llm_config)
