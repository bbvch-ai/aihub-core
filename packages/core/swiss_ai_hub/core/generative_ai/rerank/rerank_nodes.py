import asyncio

from llama_index.core.schema import NodeWithScore

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.generative_ai.rerank.rerank_request import RerankRequest
from swiss_ai_hub.core.generative_ai.resources.models.llm.reranking_model_config import RerankingModelConfig
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService


async def rerank_nodes(
    nodes: list[IngestedNode],
    query: str,
    reranking_model: RerankingModelConfig,
    user: UserIdentity | None = None,
) -> list[IngestedNode]:
    """
    Rerank a list of nodes using a reranking service via LiteLLM.

    The request is sized here, not by the callers, so a chat message that inlines an attached document, or a node
    indexed under an older ceiling, cannot reach the reranker past its window: it rejects the pair with a 400 instead
    of truncating it. A document cut to fit is cut for the request only; the result carries the node as retrieved.
    """
    if not nodes:
        return []

    api_key = await LiteLLMService.api_key_for_user(user) if user else None
    reranking_service, _ = reranking_model.to_llama_index(api_key=api_key)
    budget = await asyncio.to_thread(reranking_model.token_budget)
    nodes_with_scores = [node.to_llama_index_node_with_score() for node in nodes]
    request = await asyncio.to_thread(RerankRequest.fit, query, nodes_with_scores, budget)
    # The underlying reranker uses a blocking httpx.Client; offload to a thread so
    # the event loop can do other work while the rerank API call is in flight.
    reranked = await asyncio.to_thread(
        reranking_service.postprocess_nodes, query_str=request.query, nodes=request.nodes
    )
    as_retrieved = {node.node.node_id: node.node for node in nodes_with_scores}
    # slicing the reranked nodes manually, as the endpoint returns all nodes regardless of top_n
    return [
        IngestedNode.from_llama_index_node_with_score(
            NodeWithScore(node=as_retrieved[node.node.node_id], score=node.score)
        )
        for node in reranked[: reranking_model.top_n]
    ]
