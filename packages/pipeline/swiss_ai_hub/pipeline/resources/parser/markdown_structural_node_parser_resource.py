from dagster import ConfigurableResource, ResourceDependency
from swiss_ai_hub.core.generative_ai.document.parsers.markdown_structural_node_parser import (
    MarkdownStructuralNodeParser,
)
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_STORE_NAME

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.model_builders import embedding_config_for_bucket, llm_config_for_bucket


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
                    llm_config=my_llm_config,
                    embedding_config=my_embedding_config,
                ),
            }
        )
    """  # noqa: E501

    # Deployment defaults, used for a database that names no models of its own.
    llm_config: ResourceDependency[LLMConfig]
    embedding_config: ResourceDependency[EmbeddingModelConfig]

    def get_node_parser_for_ref_doc(
        self, ref_doc: RefDocDocument, document_store_name: str, bucket: str | None = None
    ) -> MarkdownStructuralNodeParser:
        """``bucket`` selects the knowledge database whose configured models are used, if it names any."""
        metadata = ref_doc.metadata
        metadata[DOCUMENT_STORE_NAME] = document_store_name
        llm_config = llm_config_for_bucket(bucket) if bucket else self.llm_config
        embedding_config = embedding_config_for_bucket(bucket) if bucket else self.embedding_config
        # The node ceiling comes from the embedding model that will consume the nodes, so the chunker cannot emit
        # something the model rejects. The parser resolves it per ref doc, not at Definitions build time: the lookup
        # goes over the network, and a code location must still load when LiteLLM is down.
        return MarkdownStructuralNodeParser(
            metadata=metadata,
            llm_config=llm_config,
            embedding_model_name=embedding_config.model_name,
        )
