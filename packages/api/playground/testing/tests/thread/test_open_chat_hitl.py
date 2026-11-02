from types import SimpleNamespace

import pytest
from bson import ObjectId
from swiss_ai_hub.core.events.agent import (
    HumanInTheLoopChatRequestEvent,
    HumanInTheLoopChatResponseEvent,
    HumanInTheLoopRequestEvent,
    HumanInTheLoopResponseEvent,
)
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.topic_managers import AgentTopicManager
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.api.routes.thread.thread_service import ThreadService


def _request(question: str) -> HumanInTheLoopChatRequestEvent:
    topic = AgentInstanceTopic(
        agent_class="TestAgent",
        agent_id="test-agent",
        thread_id=str(ObjectId()),
        display_id=str(ObjectId()),
        run_id=str(ObjectId()),
        event_type=AgentTopicManager.CONTROL_EVENT,
        event_name=HumanInTheLoopChatResponseEvent.event_name_from_class(),
        event_id=str(ObjectId()),
    )
    return HumanInTheLoopChatRequestEvent(question=question, topic=topic)


def _answer(request: HumanInTheLoopChatRequestEvent) -> HumanInTheLoopChatResponseEvent:
    return HumanInTheLoopChatResponseEvent(response="yes", request_event=request.model_dump())


@pytest.fixture
def thread_events(monkeypatch: pytest.MonkeyPatch):
    """Persisted requests and responses as the entity's control-event queries return them."""

    def install(requests: list[HumanInTheLoopRequestEvent], responses: list[HumanInTheLoopResponseEvent]) -> None:
        stored_requests = [SimpleNamespace(event_data=request.model_dump()) for request in requests]
        stored_responses = [SimpleNamespace(event_data=response.model_dump()) for response in responses]
        monkeypatch.setattr(
            PersistedAgentEventEntity,
            "human_in_the_loop_request_events_for_thread",
            classmethod(lambda cls, thread_id: stored_requests),
        )
        monkeypatch.setattr(
            PersistedAgentEventEntity,
            "human_in_the_loop_response_events_for_thread",
            classmethod(lambda cls, thread_id: stored_responses),
        )

    return install


def test_an_answered_form_leaves_nothing_open(thread_events) -> None:
    form = _request("Please confirm")
    thread_events([form], [_answer(form)])

    assert ThreadService.get_open_chat_hitl("thread").has_open_chat_hitl is False


def test_the_oldest_unanswered_request_is_open(thread_events) -> None:
    answered, first_open, second_open = _request("a"), _request("b"), _request("c")
    thread_events([answered, first_open, second_open], [_answer(answered)])

    result = ThreadService.get_open_chat_hitl("thread")

    assert result.has_open_chat_hitl is True
    assert result.hitl_request.event_id == first_open.event_id
