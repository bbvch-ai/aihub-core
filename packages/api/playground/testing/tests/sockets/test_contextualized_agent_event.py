from swiss_ai_hub.core.events.agent import (
    ConversationTagsEvent,
    ConversationTitleEvent,
    DisplayEvent,
    HumanInTheLoopChatRequestEvent,
    HumanInTheLoopChatResponseEvent,
    HumanInTheLoopConfirmationRequestEvent,
    HumanInTheLoopConfirmationResponseEvent,
    HumanInTheLoopInputRequestEvent,
    HumanInTheLoopInputResponseEvent,
    SuggestedFollowUpQuestionsEvent,
)
from swiss_ai_hub.core.topic_managers import AgentTopicManager
from swiss_ai_hub.core.topics import PartialAgentTopic

from swiss_ai_hub.api.sockets.events.server_to_user.contextualized_agent_event import (
    ContextualizedAgentEvent,
    DisplayEvents,
    event_discriminator,
)


class _FakeInputRequest(HumanInTheLoopInputRequestEvent):
    """Stand-in for an agent-specific input-request subclass (e.g. FollowUpQuestionRequestEvent)."""


class _FakeConfirmationRequest(HumanInTheLoopConfirmationRequestEvent):
    """Stand-in for an agent-specific confirmation-request subclass."""


class _FakeChatRequest(HumanInTheLoopChatRequestEvent):
    """Stand-in for an agent-specific chat-request subclass."""


class _FakeInputResponse(HumanInTheLoopInputResponseEvent):
    """Stand-in for an agent-specific input-response subclass."""


class _FakeConfirmationResponse(HumanInTheLoopConfirmationResponseEvent):
    """Stand-in for an agent-specific confirmation-response subclass."""


class _FakeChatResponse(HumanInTheLoopChatResponseEvent):
    """Stand-in for an agent-specific chat-response subclass."""


def _make_topic() -> PartialAgentTopic:
    return PartialAgentTopic(
        event_type=AgentTopicManager.CONTROL_EVENT,
        event_name="SomeResponseEvent",
    )


def _wrap(event: DisplayEvent) -> ContextualizedAgentEvent:
    return ContextualizedAgentEvent(
        event_display_name="x",
        event_display_description="x",
        agent_class="TestAgent",
        agent_id="test",
        thread_id="t",
        display_id="d",
        run_id="r",
        event_type="control_event",
        event_name=type(event).__name__,
        event_id="e",
        event=event,
    )


def test_display_events_union_tags_hitl_subclasses():
    """All three HITL request subclasses and their responses are in the discriminated union."""
    valid_tags = {arg.__metadata__[0].tag for arg in DisplayEvents.__args__}
    assert {
        "HumanInTheLoopInputRequestEvent",
        "HumanInTheLoopConfirmationRequestEvent",
        "HumanInTheLoopChatRequestEvent",
        "HumanInTheLoopInputResponseEvent",
        "HumanInTheLoopConfirmationResponseEvent",
        "HumanInTheLoopChatResponseEvent",
    }.issubset(valid_tags)


def test_input_request_subclass_discriminator_resolves_to_input_not_base():
    """An agent-specific Input subclass must map to HumanInTheLoopInputRequestEvent, not the base."""
    event = _FakeInputRequest(question="?", topic=_make_topic())
    assert event_discriminator(event) == "HumanInTheLoopInputRequestEvent"


def test_confirmation_request_subclass_discriminator_resolves_to_confirmation():
    event = _FakeConfirmationRequest(question="?", topic=_make_topic())
    assert event_discriminator(event) == "HumanInTheLoopConfirmationRequestEvent"


def test_chat_request_subclass_discriminator_resolves_to_chat():
    event = _FakeChatRequest(question="?", topic=_make_topic())
    assert event_discriminator(event) == "HumanInTheLoopChatRequestEvent"


def test_input_response_subclass_discriminator_resolves_to_input_response():
    """The response path was the one actually failing in production — HITL response echo from the frontend."""
    event = _FakeInputResponse(
        response="answer",
        request_event=_FakeInputRequest(question="?", topic=_make_topic()),
        topic=_make_topic(),
    )
    assert event_discriminator(event) == "HumanInTheLoopInputResponseEvent"


def test_confirmation_response_subclass_discriminator_resolves_to_confirmation_response():
    event = _FakeConfirmationResponse(
        response=True,
        request_event=_FakeConfirmationRequest(question="?", topic=_make_topic()),
        topic=_make_topic(),
    )
    assert event_discriminator(event) == "HumanInTheLoopConfirmationResponseEvent"


def test_chat_response_subclass_discriminator_resolves_to_chat_response():
    event = _FakeChatResponse(
        response="reply",
        request_event=_FakeChatRequest(question="?", topic=_make_topic()),
        topic=_make_topic(),
    )
    assert event_discriminator(event) == "HumanInTheLoopChatResponseEvent"


def test_display_events_union_tags_conversation_metadata_events():
    """The conversation-metadata display events are in the discriminated union (no silent downcast)."""
    valid_tags = {arg.__metadata__[0].tag for arg in DisplayEvents.__args__}
    assert {
        "ConversationTitleEvent",
        "ConversationTagsEvent",
        "SuggestedFollowUpQuestionsEvent",
    }.issubset(valid_tags)


def test_conversation_metadata_events_preserved_through_contextualized_dump():
    """Each metadata event survives ContextualizedAgentEvent.model_dump() with its own type and payload."""
    title = _wrap(ConversationTitleEvent(title="Weather in Ho Chi Minh City")).model_dump()["event"]
    assert title["_event_name"] == "ConversationTitleEvent"
    assert title["title"] == "Weather in Ho Chi Minh City"

    tags = _wrap(ConversationTagsEvent(tags=["Weather", "Travel"])).model_dump()["event"]
    assert tags["_event_name"] == "ConversationTagsEvent"
    assert tags["tags"] == ["Weather", "Travel"]

    follow_ups = _wrap(SuggestedFollowUpQuestionsEvent(questions=["What is the forecast?"])).model_dump()["event"]
    assert follow_ups["_event_name"] == "SuggestedFollowUpQuestionsEvent"
    assert follow_ups["questions"] == ["What is the forecast?"]


def test_agent_subclass_preserved_through_contextualized_dump():
    """ContextualizedAgentEvent.model_dump() must preserve subclass class info in the nested event."""
    event = _FakeInputRequest(question="?", topic=_make_topic())
    dumped = _wrap(event).model_dump()
    nested = dumped["event"]

    # The bug was that this was "HumanInTheLoopRequestEvent" (base class).
    assert nested["_event_name"] == "_FakeInputRequest"
    assert "HumanInTheLoopInputRequestEvent" in nested["_parent_event_names"]
    assert nested["hitl_type"] == "input"
