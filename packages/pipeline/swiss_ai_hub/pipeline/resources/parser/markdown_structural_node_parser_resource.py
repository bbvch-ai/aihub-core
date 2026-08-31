from dagster import ConfigurableResource, ResourceDependency
from swiss_ai_hub.core.generative_ai.document.parsers.markdown_structural_node_parser import (
    DEFAULT_EMBEDDING_MAX_INPUT_TOKENS,
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
        return MarkdownStructuralNodeParser(
            metadata=metadata,
            llm_config=llm_config,
            max_embedding_tokens=self._resolve_max_embedding_tokens(embedding_config),
        )

    @staticmethod
    def _resolve_max_embedding_tokens(embedding_config: EmbeddingModelConfig) -> int:
        """
        Source the node ceiling from the embedding model that will actually consume the nodes, so the chunker
        cannot emit something the model rejects.

        Resolved per ref doc rather than at Definitions build time: the lookup goes over the network, and a
        code location must still load when LiteLLM is down. LiteLLM reports null for models it holds no
        metadata for, hence the fallback.
        """
        max_input_tokens = embedding_config.get_model_info()["model_info"].get("max_input_tokens")
        return max_input_tokens or DEFAULT_EMBEDDING_MAX_INPUT_TOKENS
