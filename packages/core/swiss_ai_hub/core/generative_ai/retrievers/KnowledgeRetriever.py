from swiss_ai_hub.core.generative_ai.document.types.IngestedNode import IngestedNode
from swiss_ai_hub.core.generative_ai.retrieval.retrieve_nodes import retrieve_nodes
from swiss_ai_hub.core.generative_ai.retrieval.retrieve_parent_summary_nodes import retrieve_parent_summary_nodes
from swiss_ai_hub.core.generative_ai.retrieval.retrieve_prev_next_nodes import retrieve_prev_next_nodes
from swiss_ai_hub.core.generative_ai.retrievers.BaseRetriever import BaseRetriever
from swiss_ai_hub.core.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class KnowledgeRetriever(BaseRetriever):
    """Retriever for knowledge from a vector store (Milvus)."""

    def __init__(self, config: KnowledgeRetrieverConfig):
        super().__init__(config)
        self.config: KnowledgeRetrieverConfig = config

    @trace_fn
    async def retrieve(self, query: str, t: LocaleHandler) -> list[IngestedNode]:
        """Retrieve nodes from the vector store matching the query."""
        embed_model, _ = self.config.embed_model.to_llama_index()
        vector_store = self.config.vector_store.to_llama_index()

        nodes = retrieve_nodes(
            message=query,
            embed_model=embed_model,
            retrieve_k=self.config.retrieve_k,
            index_namespaces=self.config.vector_store.index_namespaces,
            query_mode=self.config.query_mode,
            node_types=self.config.node_types,
            vector_store=vector_store,
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
