from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.resources.models.llm.RerankingModelConfig import RerankingModelConfig


async def rerank_nodes(
    nodes: list[IngestedNode],
    query: str,
    reranking_model: RerankingModelConfig,
    top_k: int,
    max_tokens: int,
) -> list[IngestedNode]:
    """Rerank a list of nodes using a reranking service via LiteLLM."""
    if top_k <= 0:
        raise ValueError("top_k must be a positive integer")

    if not nodes:
        return []

    documents = [node.content for node in nodes]

    reranking_service = reranking_model.get_reranking_service()
    rerank_result = await reranking_service.rerank(
        query=query,
        nodes=documents,
        top_k=top_k,
        max_tokens=max_tokens,
    )

    reranked_nodes = []
    for result in rerank_result:
        reranked_nodes.append(nodes[result.index])

    return reranked_nodes
