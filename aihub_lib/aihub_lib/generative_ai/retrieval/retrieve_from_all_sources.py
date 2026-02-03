import asyncio

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.retrievers.KnowledgeRetriever import KnowledgeRetriever
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler


async def retrieve_from_all_sources(
    query: str,
    retriever_configs: list[KnowledgeRetrieverConfig],
    t: LocaleHandler,
) -> list[IngestedNode]:
    """
    Create knowledge retrievers and retrieve from all configured sources in parallel.
    """
    retrievers = [KnowledgeRetriever(config) for config in retriever_configs]

    if not retrievers:
        return []

    results = await asyncio.gather(*[retriever.retrieve(query, t) for retriever in retrievers])
    return [node for nodes in results for node in nodes]
