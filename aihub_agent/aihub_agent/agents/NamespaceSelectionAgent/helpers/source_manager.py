"""
Thread context source management for NamespaceSelectionAgent.

Provides functions to safely persist and retrieve selected sources
from ThreadContext for reuse across multiple queries in the same thread.
"""

import logging
from typing import Any

from aihub_lib.nats.events import KnowledgeSource
from pydantic import ValidationError

from aihub_agent.context.thread.ThreadContext import ThreadContext

logger = logging.getLogger(__name__)

# ThreadContext key for persisted source selection
THREAD_KEY_SELECTED_SOURCES = "namespace_selection:selected_sources"


async def get_current_sources(thread_context: ThreadContext) -> list[KnowledgeSource] | None:
    """
    Retrieve currently selected sources from thread context.

    Returns None if no sources are stored or if the stored data is corrupted.
    Corrupted data is logged and treated as a fresh start.
    """
    data: list[dict[str, Any]] | None = await thread_context.get(THREAD_KEY_SELECTED_SOURCES)
    if not data:
        return None

    try:
        return [KnowledgeSource(**s) for s in data]
    except (TypeError, ValidationError) as e:
        logger.warning(f"Failed to deserialize stored sources: {e}, starting fresh")
        return None


async def save_selected_sources(
    thread_context: ThreadContext,
    sources: list[KnowledgeSource],
) -> None:
    """Persist selected sources to thread context for future queries."""
    sources_data = [s.model_dump() for s in sources]
    await thread_context.set(THREAD_KEY_SELECTED_SOURCES, sources_data)
