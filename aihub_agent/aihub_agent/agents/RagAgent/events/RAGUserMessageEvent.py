from typing import Annotated

from aihub_lib.generative_ai.retrievers import RetrieverConfig
from aihub_lib.nats.events.user import UserMessageEvent
from pydantic import Field


class RAGUserMessageEvent(UserMessageEvent):
    """
    Start event for RAG agents with optional retriever configuration override.

    Extends UserMessageEvent with an optional `retrievers` field that allows
    callers to specify retriever configurations at runtime. When provided,
    these override the agent's configured retrievers.

    Priority chain:
    1. RAGUserMessageEvent.retrievers (if provided)
    2. RAGAgentConfig.retrievers (if provided)
    3. RetrievalAgentConfig.retrievers (fallback)
    """

    retrievers: Annotated[
        list[RetrieverConfig] | None,
        Field(description="Optional retriever configs. Overrides agent config if provided."),
    ] = None
