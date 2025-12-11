"""Helper function to retrieve from multiple configured sources in parallel."""

import asyncio

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.retrievers import RetrieverConfig, create_retriever
from aihub_lib.i18n.LocaleHandler import LocaleHandler


async def retrieve_from_all_sources(
    query: str,
    retriever_configs: list[RetrieverConfig],
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> list[IngestedNode]:
    """
    Create retrievers and retrieve from all configured sources in parallel.
    """
    retrievers = []
    for config in retriever_configs:
        retriever = create_retriever(config)
        source_name = t(f"agent.retriever.{config.retriever_type.value}")
        await displayer.display_thought(t("agent.thought.retrieving_from", source=source_name))
        retrievers.append(retriever)

    if not retrievers:
        return []

    results = await asyncio.gather(*[retriever.retrieve(query, t) for retriever in retrievers])
    return [node for nodes in results for node in nodes]
