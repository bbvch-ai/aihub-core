import asyncio

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.retrievers.BaseRetrieverConfig import BaseRetrieverConfig
from aihub_lib.generative_ai.retrievers.create_retriever import create_retriever
from aihub_lib.i18n.LocaleHandler import LocaleHandler


async def retrieve_from_all_sources(
    query: str,
    retriever_configs: list[BaseRetrieverConfig],
    t: LocaleHandler,
) -> list[IngestedNode]:
    """
    Create retrievers and retrieve from all configured sources in parallel.
    """
    retrievers = []
    for config in retriever_configs:
        retriever = create_retriever(config)
        retrievers.append(retriever)

    if not retrievers:
        return []

    results = await asyncio.gather(*[retriever.retrieve(query, t) for retriever in retrievers])
    return [node for nodes in results for node in nodes]
