from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.retrievers import RetrieverConfig
from aihub_lib.generative_ai.utils.retrieve_from_all_sources import retrieve_from_all_sources
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent


async def execute_retrieve(
    query: str,
    retrievers: list[RetrieverConfig],
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> RetrieverEvent:
    """
    Retrieves relevant nodes from multiple knowledge sources in parallel.
    """
    all_nodes = await retrieve_from_all_sources(query, retrievers, displayer, t)
    nodes_with_score = [node.to_llama_index_node_with_score() for node in all_nodes]
    return RetrieverEvent.from_nodes(nodes_with_score)
