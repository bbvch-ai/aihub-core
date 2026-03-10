import asyncio
import logging

from swiss_ai_hub.core.generative_ai.document.types.IngestedNode import IngestedNode
from swiss_ai_hub.core.generative_ai.retrievers.KnowledgeRetriever import KnowledgeRetriever
from swiss_ai_hub.core.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler

logger = logging.getLogger(__name__)


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
        logger.warning("No retrievers configured, skipping retrieval.")
        return []

    results = await asyncio.gather(*[retriever.retrieve(query, t) for retriever in retrievers])
    return [node for nodes in results for node in nodes]
