"""Unit tests for the decoupled memory-storage events (issue #1179).

`MemoryStorageRequestedEvent` must be a pure control event (no display half — otherwise a delegation step
would render in chat after the answer) and must round-trip through polymorphic (de)serialization with its
nested `StoreUserMemoryRequestedEvent`.
"""

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.events.agent.memory.request.memory_storage_requested_event import (
    MemoryStorageRequestedEvent,
)
from swiss_ai_hub.core.events.agent.memory.request.store_user_memory_requested_event import (
    StoreUserMemoryRequestedEvent,
)
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user


def _request() -> MemoryStorageRequestedEvent:
    return MemoryStorageRequestedEvent(
        start_event=StoreUserMemoryRequestedEvent(
            user=fake_user(),
            messages=[ChatMessage(role=MessageRole.USER, content="remember I like dark mode")],
            locale="en",
            origin_thread_id="t1",
            origin_display_id="d1",
            origin_run_id="r1",
            origin_agent_class="RAGAgent",
            origin_agent_id="hr",
            origin_agent_name=LocaleString(en="HR"),
            origin_agent_description=LocaleString(en="HR agent"),
        ),
        target_agent_class="MemoryWriterAgent",
        target_agent_id="memory-writer",
    )


def test_is_control_event_not_display_event():
    """Must be control-only so the dispatcher never emits a visible delegation step (the #1179 symptom)."""
    event = _request()
    assert event.is_control_event
    assert not event.is_display_event
    assert event.is_memory_storage_request_event


def test_round_trip_preserves_nested_start_event():
    event = _request()
    restored = BaseEvent.deserialize_event(event.model_dump())
    assert isinstance(restored, MemoryStorageRequestedEvent)
    assert isinstance(restored.start_event, StoreUserMemoryRequestedEvent)
    assert restored.target_agent_id == "memory-writer"
    assert restored.start_event.origin_agent_class == "RAGAgent"
    assert restored.start_event.messages[0].content == "remember I like dark mode"


def test_store_request_is_a_start_event():
    """The writer's start event must be recognized as a start event so it triggers a run."""
    assert _request().start_event.is_start_event
