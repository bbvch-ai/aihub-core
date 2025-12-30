import logging

from llama_index.core.schema import NodeWithScore

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.retrievers.BaseRetriever import BaseRetriever
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.generative_ai.utils.retrieve_nodes import retrieve_nodes
from aihub_lib.generative_ai.utils.retrieve_parent_summary_nodes import retrieve_parent_summary_nodes
from aihub_lib.generative_ai.utils.retrieve_prev_next_nodes import retrieve_prev_next_nodes
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE, SOURCE

logger = logging.getLogger(__name__)

# File extensions that indicate a standalone image file (not embedded in a document)
_STANDALONE_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".svg"}


def _is_standalone_image(source: str) -> bool:
    """Check if the source is a standalone image file based on its extension."""
    source_lower = source.lower()
    return any(source_lower.endswith(ext) for ext in _STANDALONE_IMAGE_EXTENSIONS)


class KnowledgeRetriever(BaseRetriever):
    """Retriever for knowledge from a vector store (Milvus)."""

    def __init__(self, config: KnowledgeRetrieverConfig):
        super().__init__(config)
        self.config: KnowledgeRetrieverConfig = config

    def _filter_excluded_content_types(self, nodes: list[NodeWithScore]) -> list[NodeWithScore]:
        """Filter out nodes with excluded content types, preserving standalone images."""
        if not self.config.exclude_content_types:
            return nodes

        filtered = []
        for node in nodes:
            content_type = node.node.metadata.get(NODE_CONTENT_TYPE)
            source = node.node.metadata.get(SOURCE, "")

            # Keep node if:
            # 1. Its content type is not in the exclude list, OR
            # 2. It's from a standalone image file (we always keep those)
            if content_type not in self.config.exclude_content_types or _is_standalone_image(source):
                filtered.append(node)

        return filtered

    @trace_fn
    async def retrieve(self, query: str, t: LocaleHandler) -> list[IngestedNode]:
        """Retrieve nodes from the vector store matching the query."""
        embed_model, _ = self.config.embed_model.to_llama_index()
        vector_store = self.config.vector_store.to_llama_index()

        nodes = retrieve_nodes(
            message=query,
            embed_model=embed_model,
            retrieve_k=self.config.retrieve_k,
            index_namespaces=self.config.index_namespaces,
            query_mode=self.config.query_mode,
            node_types=self.config.node_types,
            vector_store=vector_store,
        )

        if not nodes:
            return []

        # Filter out excluded content types before prev/next retrieval
        # This allows excluded types to still be retrieved via prev/next context
        original_count = len(nodes)
        nodes = self._filter_excluded_content_types(nodes)
        if len(nodes) < original_count:
            logger.debug(
                f"Filtered {original_count - len(nodes)} nodes with excluded content types "
                f"({self.config.exclude_content_types}), {len(nodes)} remaining"
            )

        if not nodes:
            return []

        if self.config.retrieve_prev_next:
            nodes = retrieve_prev_next_nodes(
                nodes=nodes,
                vector_store=vector_store,
                num_nodes=self.config.retrieve_prev_next.num_nodes,
                prev_next_mode=self.config.retrieve_prev_next.mode,
            )

        if self.config.retrieve_summaries:
            nodes = retrieve_parent_summary_nodes(
                nodes=nodes,
                vector_store=vector_store,
                max_levels=self.config.retrieve_summaries.max_parent_levels,
            )

        return [IngestedNode.from_llama_index_node_with_score(node) for node in nodes]
