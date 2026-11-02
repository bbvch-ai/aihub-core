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
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_response_event import (
    HumanInTheLoopResponseEvent,
)
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
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
    return _install_thread(monkeypatch, [open_request], [], user_id)


def _install_thread(
    monkeypatch: pytest.MonkeyPatch,
    requests: list[HumanInTheLoopRequestEvent],
    responses: list[HumanInTheLoopResponseEvent],
    user_id: str,
) -> SimpleNamespace:
    """The thread's persisted requests and responses, as the entity's control-event queries return them."""
    thread = SimpleNamespace(id=ObjectId(), users=[User(user_id=user_id)])
    persisted_requests = [SimpleNamespace(event_data=request.model_dump()) for request in requests]
    persisted_responses = [SimpleNamespace(event_data=response.model_dump()) for response in responses]

    monkeypatch.setattr(ThreadEntity, "create_thread", classmethod(lambda cls, *a, **kw: thread))
    monkeypatch.setattr(
        PersistedAgentEventEntity,
        "human_in_the_loop_request_events_for_thread",
        classmethod(lambda cls, thread_id: persisted_requests),
    )
    monkeypatch.setattr(
        PersistedAgentEventEntity,
        "human_in_the_loop_response_events_for_thread",
        classmethod(lambda cls, thread_id: persisted_responses),
    )
    return thread


def _chat_request(question: str) -> HumanInTheLoopChatRequestEvent:
    topic = _build_hitl_topic(event_name=HumanInTheLoopChatResponseEvent.event_name_from_class())
    return HumanInTheLoopChatRequestEvent(question=question, topic=topic)


def _answer(request: HumanInTheLoopChatRequestEvent, text: str) -> HumanInTheLoopChatResponseEvent:
    return HumanInTheLoopChatResponseEvent(response=text, request_event=request.model_dump())


def _send(text: str):
    return ChatService._initialize_interaction(
        user=fake_user(),
        agent_class=AGENT_CLASS,
        agent_id=AGENT_ID,
        messages=[ChatMessage(role=MessageRole.USER, content=text)],
    )[0].event


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


def test_a_message_after_an_answered_form_starts_a_new_run(monkeypatch: pytest.MonkeyPatch) -> None:
    form = _chat_request("Please confirm the request")
    _install_thread(monkeypatch, [form], [_answer(form, '{"where": {"type": "option", "option_index": 0}}')], "u")

    assert isinstance(_send("Extract the 2024 invoices too"), UserMessageEvent)


def test_a_reply_answers_the_open_request_not_an_answered_one(monkeypatch: pytest.MonkeyPatch) -> None:
    first = _chat_request("First form")
    second = _chat_request("Second form")
    _install_thread(monkeypatch, [first, second], [_answer(first, "yes")], "u")

    event = _send("yes")

    assert isinstance(event, HumanInTheLoopChatResponseEvent)
    assert event.request_event.event_id == second.event_id


def test_a_reply_answers_the_open_request_even_when_a_newer_one_was_answered(monkeypatch: pytest.MonkeyPatch) -> None:
    older = _chat_request("Older form")
    newer = _chat_request("Newer form")
    _install_thread(monkeypatch, [older, newer], [_answer(newer, "yes")], "u")

    event = _send("yes")

    assert isinstance(event, HumanInTheLoopChatResponseEvent)
    assert event.request_event.event_id == older.event_id
