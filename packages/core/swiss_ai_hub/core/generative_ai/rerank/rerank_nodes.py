import asyncio

from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.generative_ai.resources.models.llm.reranking_model_config import RerankingModelConfig


async def rerank_nodes(
    nodes: list[IngestedNode],
    query: str,
    reranking_model: RerankingModelConfig,
) -> list[IngestedNode]:
    """Rerank a list of nodes using a reranking service via LiteLLM."""
    if not nodes:
        return []

    reranking_service, _ = reranking_model.to_llama_index()
    nodes_with_scores = [node.to_llama_index_node_with_score() for node in nodes]
    # The underlying reranker uses a blocking httpx.Client; offload to a thread so
    # the event loop can do other work while the rerank API call is in flight.
    reranked = await asyncio.to_thread(reranking_service.postprocess_nodes, query_str=query, nodes=nodes_with_scores)
    # slicing the reranked nodes manually, as the endpoint returns all nodes regardless of top_n
    reranked_nodes = reranked[: reranking_model.top_n]
    result_nodes = [IngestedNode.from_llama_index_node_with_score(node) for node in reranked_nodes]
    return result_nodes
