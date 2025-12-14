from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.resources.models.llm.RerankingModelConfig import RerankingModelConfig
from aihub_lib.generative_ai.utils.rerank_nodes import rerank_nodes
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.semantic.reranker import RerankerEvent


async def execute_rerank_nodes(
    nodes: list[IngestedNode],
    query: str,
    reranking_model: RerankingModelConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    reranking_enabled: bool = True,
) -> RerankerEvent:
    """
    Reranks retrieved documents using a dedicated reranking model.
    """
    await displayer.display_thought(t("agent.thought.reranking_results"))

    reranked_nodes = await rerank_nodes(
        nodes=nodes,
        query=query,
        reranking_model=reranking_model,
    )

    return RerankerEvent(
        query=query,
        rerank_model_name=reranking_model.model_name,
        top_n=reranking_model.top_n,
        input_nodes=nodes,
        output_nodes=reranked_nodes,
        reranked=reranking_enabled,
    )
