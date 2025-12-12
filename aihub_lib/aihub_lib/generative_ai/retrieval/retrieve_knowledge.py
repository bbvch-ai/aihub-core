from aihub_lib.agents.step_configs import KnowledgeRetrievalStepConfig
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.utils.retrieve_nodes import retrieve_nodes
from aihub_lib.generative_ai.utils.retrieve_parent_summary_nodes import retrieve_parent_summary_nodes
from aihub_lib.generative_ai.utils.retrieve_prev_next_nodes import retrieve_prev_next_nodes
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


@trace_fn
async def retrieve_knowledge(
    query: str,
    config: KnowledgeRetrievalStepConfig,
    namespaces: list[str] | None = None,
) -> list[IngestedNode]:
    """
    Retrieve knowledge nodes from a vector store.

    Args:
        query: The search query
        config: Step configuration with retrieval settings
        namespaces: Optional override for namespaces (uses config.namespaces if not provided)

    Returns:
        List of retrieved nodes
    """
    effective_namespaces = namespaces or config.namespaces

    embed_model, _ = config.embed_model.to_llama_index()
    vector_store = config.vector_store.to_llama_index()

    nodes = retrieve_nodes(
        message=query,
        embed_model=embed_model,
        retrieve_k=config.retrieve_k,
        index_namespaces=effective_namespaces,
        query_mode=config.query_mode,
        node_types=list(config.node_types),
        vector_store=vector_store,
    )

    if not nodes:
        return []

    if config.retrieve_prev_next:
        nodes = retrieve_prev_next_nodes(
            nodes=nodes,
            vector_store=vector_store,
            num_nodes=config.retrieve_prev_next.num_nodes,
            prev_next_mode=config.retrieve_prev_next.mode,
        )

    if config.retrieve_summaries:
        nodes = retrieve_parent_summary_nodes(
            nodes=nodes,
            vector_store=vector_store,
            max_levels=config.retrieve_summaries.max_parent_levels,
        )

    return [IngestedNode.from_llama_index_node_with_score(node) for node in nodes]
