from types import SimpleNamespace

import pytest
from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_chat_request_event import (
    HumanInTheLoopChatRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_confirmation_request_event import (
    HumanInTheLoopConfirmationRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_input_request_event import (
    HumanInTheLoopInputRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_request_event import (
    HumanInTheLoopRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_chat_response_event import (
    HumanInTheLoopChatResponseEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_input_response_event import (
    HumanInTheLoopInputResponseEvent,
)
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import ThreadEntity, User
from swiss_ai_hub.core.routes.chat.chat_service import ChatService
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager
from swiss_ai_hub.core.topics.agents.agent_instance_topic import AgentInstanceTopic

AGENT_CLASS = "TestAgent"
AGENT_ID = "test-agent"


def _build_hitl_topic(event_name: str) -> AgentInstanceTopic:
    return AgentInstanceTopic(
        agent_class=AGENT_CLASS,
        agent_id=AGENT_ID,
        thread_id=str(ObjectId()),
        display_id=str(ObjectId()),
        run_id=str(ObjectId()),
        event_type=AgentTopicManager.CONTROL_EVENT,
        event_name=event_name,
        event_id=str(ObjectId()),
    )


def _install_stubs(
    monkeypatch: pytest.MonkeyPatch,
    open_request: HumanInTheLoopRequestEvent,
    user_id: str,
) -> SimpleNamespace:
    thread = SimpleNamespace(id=ObjectId(), users=[User(user_id=user_id)])

    def _create_thread(*args, **kwargs):
        return thread

    persisted = SimpleNamespace(event_data=open_request.model_dump())

    monkeypatch.setattr(ThreadEntity, "create_thread", classmethod(lambda cls, *a, **kw: thread))
    monkeypatch.setattr(
        PersistedAgentEventEntity,
        "human_in_the_loop_request_events_for_thread",
        classmethod(lambda cls, thread_id: [persisted]),
    )
    monkeypatch.setattr(
        PersistedAgentEventEntity,
        "human_in_the_loop_response_events_for_thread",
        classmethod(lambda cls, thread_id: []),
    )
    return thread


@pytest.mark.parametrize(
    ("request_cls", "expected_response_cls"),
    [
        (HumanInTheLoopInputRequestEvent, HumanInTheLoopInputResponseEvent),
        (HumanInTheLoopChatRequestEvent, HumanInTheLoopChatResponseEvent),
    ],
)
def test_hitl_dispatch_selects_matching_response_class(
    monkeypatch: pytest.MonkeyPatch,
    request_cls: type[HumanInTheLoopRequestEvent],
    expected_response_cls: type,
) -> None:
    user = fake_user()
    topic = _build_hitl_topic(event_name=expected_response_cls.event_name_from_class())
    open_request = request_cls(question="Please respond", topic=topic)
    _install_stubs(monkeypatch, open_request, user.id)

    external_event, _ = ChatService._initialize_interaction(
        user=user,
        agent_class=AGENT_CLASS,
        agent_id=AGENT_ID,
        messages=[ChatMessage(role=MessageRole.USER, content="my reply")],
    )

    inner = external_event.event
    assert isinstance(inner, expected_response_cls)
    assert inner.response == "my reply"
    assert inner._parent_event_names == expected_response_cls.parent_event_names_from_class()
    assert isinstance(inner.request_event, request_cls)


def test_hitl_dispatch_rejects_unsupported_request_type(monkeypatch: pytest.MonkeyPatch) -> None:
    user = fake_user()
    topic = _build_hitl_topic(event_name="HumanInTheLoopConfirmationResponseEvent")
    open_request = HumanInTheLoopConfirmationRequestEvent(question="Proceed?", topic=topic)
    _install_stubs(monkeypatch, open_request, user.id)

    with pytest.raises(ValueError, match="HumanInTheLoopConfirmationRequestEvent"):
        ChatService._initialize_interaction(
            user=user,
            agent_class=AGENT_CLASS,
            agent_id=AGENT_ID,
            messages=[ChatMessage(role=MessageRole.USER, content="yes")],
        )
