"""A delegated run answers the run that delegated it when it ends, from its own dispatcher, through JetStream."""

from types import SimpleNamespace
from typing import Any

import pytest
from swiss_ai_hub.core.events.agent import AgentDelegation, ExceptionEvent, StopEvent
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.dispatchers.agent_dispatcher import AgentDispatcher

CALLER = AgentInstanceTopic(
    agent_class="UniversalAgent",
    agent_id="assistant",
    thread_id="caller-thread",
    display_id="caller-display",
    run_id="caller-run",
    event_type="control_event",
    event_name="StartEvent",
    event_id="event",
)


class _RunContext:
    def __init__(self, values: dict[str, Any]) -> None:
        self.values = values

    async def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)


def _dispatcher() -> SimpleNamespace:
    published = []

    async def publish_on(event, topic_manager) -> None:
        published.append((event, topic_manager))

    return SimpleNamespace(_DELEGATED_BY_KEY="delegated_by", _publish_on=publish_on, published=published)


def _delegated() -> _RunContext:
    delegation = AgentDelegation(caller=CALLER, request_event_id="request", depth=1)
    return _RunContext({"delegated_by": delegation.model_dump(mode="json")})


@pytest.mark.asyncio
async def test_a_stop_answers_the_caller_s_run():
    dispatcher = _dispatcher()

    await AgentDispatcher._answer_delegating_run(dispatcher, StopEvent(), _delegated())

    [(answer, topic_manager)] = dispatcher.published
    assert answer.is_aitl_response_event
    assert answer.request_event_id == "request"
    assert topic_manager.get_subject_for_control_event_in_thread(answer.event_name, answer.event_id).startswith(
        "agent.UniversalAgent.assistant.caller-thread.caller-display.caller-run.control_event."
    )


@pytest.mark.asyncio
async def test_a_failure_answers_the_caller_s_run_as_an_exception():
    dispatcher = _dispatcher()

    await AgentDispatcher._answer_delegating_run(dispatcher, ExceptionEvent(message="boom"), _delegated())

    [(answer, _)] = dispatcher.published
    assert answer.is_aitl_exception_event
    assert answer.exception_event.message == "boom"


@pytest.mark.asyncio
async def test_a_run_nobody_delegated_answers_nobody():
    dispatcher = _dispatcher()

    await AgentDispatcher._answer_delegating_run(dispatcher, StopEvent(), _RunContext({}))

    assert dispatcher.published == []
