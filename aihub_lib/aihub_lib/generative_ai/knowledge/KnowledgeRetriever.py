"""Retriever implementation using vector store for semantic search."""

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.knowledge.BaseRetriever import BaseRetriever
from aihub_lib.generative_ai.knowledge.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.generative_ai.utils.retrieve_nodes import retrieve_nodes
from aihub_lib.generative_ai.utils.retrieve_prev_next_nodes import retrieve_prev_next_nodes
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class KnowledgeRetriever(BaseRetriever):
    """
    Retriever implementation using vector store (Milvus) for semantic search.

    Wraps the existing retrieve_nodes() utility to provide a consistent
    interface for the RAGAgent workflow.
    """

    def __init__(self, config: KnowledgeRetrieverConfig) -> None:
        super().__init__(config)
        self._config = config

    @trace_fn
    async def retrieve(self, query: str) -> list[IngestedNode]:
        """
        Retrieve relevant nodes using vector similarity search.

        Args:
            query: The search query string

        Returns:
            List of IngestedNode objects from the vector store
        """
        embedding, _ = self._config.embed_model.to_llama_index()
        vector_store = self._config.vector_store.to_llama_index()

        nodes = retrieve_nodes(
            message=query,
            retrieve_k=self._config.retrieve_k,
            embed_model=embedding,
            index_namespaces=self._config.index_namespaces,
            query_mode=self._config.query_mode,
            node_types=list(self._config.node_types),
            vector_store=vector_store,
        )

        if self._config.retrieve_prev_next and nodes:
            nodes = retrieve_prev_next_nodes(
                vector_store=vector_store,
                nodes=nodes,
                num_nodes=self._config.retrieve_prev_next.num_nodes,
                prev_next_mode=self._config.retrieve_prev_next.mode,
            )

        if not nodes:
            return []

        return [IngestedNode.from_llama_index_node_with_score(n) for n in nodes]
