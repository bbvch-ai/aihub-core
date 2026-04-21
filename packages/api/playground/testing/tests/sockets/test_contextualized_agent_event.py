"""Regression tests for HITL subclass preservation through ContextualizedAgentEvent.

Bug history: PR #841 (2026-01-05) introduced HumanInTheLoop{Input,Confirmation,Chat}RequestEvent
subclasses but did not add them to the `DisplayEvents` discriminated union in
`contextualized_agent_event.py`. As a result, any agent-specific HITL subclass fell through
to the base `HumanInTheLoopRequestEvent` tag and got downcast during WebSocket serialization.
The frontend then echoed the downgraded event back in its POST body; the agent-side outer
validator (`FollowUpQuestionResponseEvent.request_event: HumanInTheLoopInputRequestEvent`)
rejected the base-class instance, silently dropping the message and hanging the run.
"""

from swiss_ai_hub.core.events.agent import (
    HumanInTheLoopChatRequestEvent,
    HumanInTheLoopConfirmationRequestEvent,
    HumanInTheLoopInputRequestEvent,
)
from swiss_ai_hub.core.topic_managers import AgentTopicManager
from swiss_ai_hub.core.topics import PartialAgentTopic

from swiss_ai_hub.api.sockets.events.server_to_user.contextualized_agent_event import (
    ContextualizedAgentEvent,
    DisplayEvents,
    event_discriminator,
)


class _TestInputRequest(HumanInTheLoopInputRequestEvent):
    """Stand-in for an agent-specific input-request subclass (e.g. FollowUpQuestionRequestEvent)."""


class _TestConfirmationRequest(HumanInTheLoopConfirmationRequestEvent):
    """Stand-in for an agent-specific confirmation-request subclass."""


class _TestChatRequest(HumanInTheLoopChatRequestEvent):
    """Stand-in for an agent-specific chat-request subclass."""


def _make_topic() -> PartialAgentTopic:
    return PartialAgentTopic(
        event_type=AgentTopicManager.CONTROL_EVENT,
        event_name="SomeResponseEvent",
    )


def _wrap(event) -> ContextualizedAgentEvent:
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


def test_input_subclass_discriminator_resolves_to_input_not_base():
    """An agent-specific Input subclass must map to HumanInTheLoopInputRequestEvent, not the base."""
    event = _TestInputRequest(question="?", topic=_make_topic())
    assert event_discriminator(event) == "HumanInTheLoopInputRequestEvent"


def test_confirmation_subclass_discriminator_resolves_to_confirmation():
    event = _TestConfirmationRequest(question="?", topic=_make_topic())
    assert event_discriminator(event) == "HumanInTheLoopConfirmationRequestEvent"


def test_chat_subclass_discriminator_resolves_to_chat():
    event = _TestChatRequest(question="?", topic=_make_topic())
    assert event_discriminator(event) == "HumanInTheLoopChatRequestEvent"


def test_agent_subclass_preserved_through_contextualized_dump():
    """ContextualizedAgentEvent.model_dump() must preserve subclass class info in the nested event."""
    event = _TestInputRequest(question="?", topic=_make_topic())
    dumped = _wrap(event).model_dump()
    nested = dumped["event"]

    # The bug was that this was "HumanInTheLoopRequestEvent" (base class).
    assert nested["_event_name"] == "_TestInputRequest"
    assert "HumanInTheLoopInputRequestEvent" in nested["_parent_event_names"]
    assert nested["hitl_type"] == "input"
