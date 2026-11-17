"""A run's questions are answered by the user who started it: another member of a shared thread cannot answer for
them, while answers the platform itself sends carry no responder and pass."""

from typing import Any

import pytest
from swiss_ai_hub.core.events.agent import (
    HumanInTheLoopConfirmationRequestEvent,
    HumanInTheLoopConfirmationResponseEvent,
    StopEvent,
)
from swiss_ai_hub.core.topics import AgentInstanceTopic, PartialAgentTopic

from swiss_ai_hub.agent.dispatchers.agent_dispatcher import AgentDispatcher

TOPIC = AgentInstanceTopic(
    agent_class="LoopAgent",
    agent_id="loop",
    thread_id="thread",
    display_id="display",
    run_id="run",
    event_type="control_event",
    event_name="HumanInTheLoopConfirmationResponseEvent",
    event_id="event",
)


class _RunContext:
    def __init__(self, user: dict | None) -> None:
        self.user = user

    async def get(self, key: str, default: Any = None) -> Any:
        return self.user if key == "user" else default


def _answer(responded_by: str | None) -> HumanInTheLoopConfirmationResponseEvent:
    request = HumanInTheLoopConfirmationRequestEvent(
        question="Go?", topic=PartialAgentTopic(event_type="control_event", event_name="x")
    )
    return HumanInTheLoopConfirmationResponseEvent(response=True, request_event=request, responded_by=responded_by)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("responded_by", "run_user", "accepted"),
    [
        ("alice", {"id": "alice"}, True),
        ("bob", {"id": "alice"}, False),
        (None, {"id": "alice"}, True),
        ("bob", None, True),
    ],
)
async def test_only_the_run_s_user_answers_its_questions(responded_by, run_user, accepted):
    result = await AgentDispatcher._answered_by_run_user(_answer(responded_by), _RunContext(run_user), TOPIC)

    assert result is accepted


@pytest.mark.asyncio
async def test_other_events_are_not_checked():
    event = StopEvent()

    assert await AgentDispatcher._answered_by_run_user(event, _RunContext({"id": "alice"}), TOPIC)
