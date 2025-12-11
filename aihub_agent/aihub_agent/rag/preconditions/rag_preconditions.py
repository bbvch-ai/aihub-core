"""Shared precondition functions for RAG workflows."""

from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent

from aihub_agent.workflow.decorators.precondition import precondition


@precondition()
async def reranking_enabled(event: RetrieverEvent, config) -> bool:
    """Precondition to check if reranking is enabled."""
    return isinstance(event, RetrieverEvent) and config.reranking_config.enabled


@precondition()
async def reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, config) -> bool:
    """Precondition to ensure we only order nodes after reranking is complete (or if reranking is disabled)."""
    # If reranking is disabled, we can proceed with RetrieverEvent
    if not config.reranking_config.enabled:
        return isinstance(event, RetrieverEvent)
    # If reranking is enabled, we must wait for RerankerEvent
    return isinstance(event, RerankerEvent)
