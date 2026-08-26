import asyncio
import logging

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.generative_ai.retrievers.knowledge_retriever import KnowledgeRetriever
from swiss_ai_hub.core.generative_ai.retrievers.retrieval_runtime_config import RetrievalRuntimeConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

logger = logging.getLogger(__name__)


async def retrieve_from_all_sources(
    query: str,
    runtime_configs: list[RetrievalRuntimeConfig],
    t: LocaleHandler,
    user: UserIdentity | None = None,
) -> list[IngestedNode]:
    """
    Create knowledge retrievers and retrieve from all configured sources in parallel.
    """
    retrievers = [
        KnowledgeRetriever(rc.config, additional_metadata_filters=rc.additional_metadata_filters)
        for rc in runtime_configs
    ]

    if not retrievers:
        logger.warning("No retrievers configured, skipping retrieval.")
        return []

    results = await asyncio.gather(*[retriever.retrieve(query, t, user) for retriever in retrievers])
    return [node for nodes in results for node in nodes]
