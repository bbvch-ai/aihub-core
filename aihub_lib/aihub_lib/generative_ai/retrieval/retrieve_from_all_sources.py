import asyncio
import logging

from pymilvus import MilvusClient

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.retrievers.KnowledgeRetriever import KnowledgeRetriever
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler

logger = logging.getLogger(__name__)


async def retrieve_from_all_sources(
    query: str,
    retriever_configs: list[KnowledgeRetrieverConfig],
    t: LocaleHandler,
    milvus_client: MilvusClient | None = None,
) -> list[IngestedNode]:
    """
    Create knowledge retrievers and retrieve from all configured sources in parallel.

    When a shared milvus_client is provided, all retrievers reuse that connection
    instead of creating individual ones.
    """
    retrievers = [KnowledgeRetriever(config, milvus_client=milvus_client) for config in retriever_configs]

    if not retrievers:
        logger.warning("No retrievers configured, skipping retrieval.")
        return []

    results = await asyncio.gather(*[retriever.retrieve(query, t) for retriever in retrievers])
    return [node for nodes in results for node in nodes]
