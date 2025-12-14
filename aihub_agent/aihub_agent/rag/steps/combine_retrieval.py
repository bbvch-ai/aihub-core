"""Extracted function for combining retrieval results."""

from typing import Literal

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.resources.models.llm.RerankingModelConfig import RerankingModelConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events import AgentInTheLoop, RetrievalResponseEvent

from aihub_agent.rag.events import CombinedRetrievalEvent
from aihub_agent.rag.steps.order_nodes import execute_order_nodes_by_documents
from aihub_agent.rag.steps.rerank import execute_rerank_nodes


async def execute_combine_retrieval_results(
    query: str,
    locale: Literal["de", "en", "fr", "it"],
    t: LocaleHandler,
    displayer: EventDisplayer,
    retrieval_responses: list[AgentInTheLoop.response],
    reranking_enabled: bool = False,
    reranking_model: RerankingModelConfig | None = None,
) -> CombinedRetrievalEvent:
    """Combines results from all retrieval agents and applies shared reranking."""
    all_nodes: list[IngestedNode] = []
    agent_ids: list[str] = []
    retrieval_types: set[str] = set()

    for response in retrieval_responses:
        if isinstance(response.stop_event, RetrievalResponseEvent):
            all_nodes.extend(response.stop_event.nodes)
            agent_ids.append(response.stop_event.agent_id)
            retrieval_types.add(response.stop_event.retrieval_type)

    if reranking_enabled and all_nodes:
        reranker_event = await execute_rerank_nodes(
            nodes=all_nodes,
            query=query,
            reranking_model=reranking_model,
            displayer=displayer,
            t=t.in_locale(locale),
            reranking_enabled=True,
        )
        all_nodes = reranker_event.output_nodes

    order_event = await execute_order_nodes_by_documents(
        nodes=all_nodes,
        t=t.in_locale(locale),
        displayer=displayer,
        context_prompt=None,
    )

    return CombinedRetrievalEvent(
        context_message=order_event.context_message,
        nodes=all_nodes,
        knowledge_agent_ids=agent_ids,
        has_insights="insight" in retrieval_types,
    )
