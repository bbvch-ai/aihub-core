"""
Unit coverage for ThreadTitlePersister — the long-lived subscriber handler that ties a
ConversationTitleEvent to ThreadEntity.name. It replaced per-request aggregator branches that
unsubscribed on the run's stop event, silently dropping a title emitted concurrently with the
answer (permanently, since the producer-side once-per-thread flag is set on publish).
"""

import inspect
from unittest.mock import patch

import pytest
from swiss_ai_hub.core.events.agent import ConversationTitleEvent, ThoughtEvent
from swiss_ai_hub.core.persistence import ThreadEntity
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.api.persistance.threads.thread_title_persister import ThreadTitlePersister


def _topic() -> AgentInstanceTopic:
    return AgentInstanceTopic(
        agent_class="RAGAgent",
        agent_id="test-rag",
        thread_id="thread-123",
        display_id="display-1",
        run_id="run-1",
        event_type="display_event",
        event_name="ConversationTitleEvent",
        event_id="event-1",
    )


@pytest.mark.asyncio
async def test_title_event_persists_thread_name():
    with patch.object(ThreadEntity, "update_thread_name") as update_thread_name:
        await ThreadTitlePersister.persist_thread_title(ConversationTitleEvent(title="Weather in Zurich"), _topic())

    update_thread_name.assert_called_once_with("thread-123", "Weather in Zurich")


@pytest.mark.asyncio
async def test_non_title_display_event_is_ignored():
    with patch.object(ThreadEntity, "update_thread_name") as update_thread_name:
        await ThreadTitlePersister.persist_thread_title(ThoughtEvent(reasoning_content="thinking..."), _topic())

    update_thread_name.assert_not_called()


def test_lifetime_manager_registers_the_persister():
    """After the per-request aggregator branches were removed, this subscriber is the ONLY code path
    that persists titles — guard against it being silently de-registered."""
    from swiss_ai_hub.api.runners.lifetime import lifetime_manager

    assert "ThreadTitlePersister.persist_thread_title" in inspect.getsource(lifetime_manager), (
        "lifetime_manager must register a long-lived subscriber with ThreadTitlePersister.persist_thread_title — "
        "no other code path persists ConversationTitleEvent onto the thread"
    )
