"""Deadlines of in-the-loop requests, kept by NATS: armed as a scheduled message, settled by whichever of answer and
timeout arrives first, cancelled by the answer."""

import json
from typing import Any

import pytest
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoop,
    HumanInTheLoop,
    HumanInTheLoopConfirmationResponseEvent,
    StartEvent,
    StopEvent,
)
from swiss_ai_hub.core.topic_managers import AgentClassTopicManager, AgentThreadTopicManager

from swiss_ai_hub.agent.dispatchers.in_the_loop_deadlines import InTheLoopDeadlines


class _RunContext:
    def __init__(self) -> None:
        self.values: dict[str, Any] = {}

    async def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        self.values[key] = value

    async def set_if_absent(self, key: str, value: Any) -> bool:
        if key in self.values:
            return False
        self.values[key] = value
        return True


class _JetStream:
    def __init__(self) -> None:
        self.published: list[tuple[str, bytes, dict[str, str]]] = []
        self.purged: list[tuple[str, str]] = []

    async def publish(self, subject: str, payload: bytes, headers: dict[str, str]) -> None:
        self.published.append((subject, payload, headers))

    async def purge_stream(self, name: str, subject: str) -> None:
        self.purged.append((name, subject))


THREAD = AgentThreadTopicManager(
    agent_class="LoopAgent", agent_id="loop", thread_id="thread", display_id="display", run_id="run"
)


def _deadlines() -> tuple[InTheLoopDeadlines, _JetStream]:
    js = _JetStream()
    return InTheLoopDeadlines(js, AgentClassTopicManager(agent_class="LoopAgent")), js


@pytest.mark.asyncio
async def test_a_request_without_timeout_schedules_nothing():
    deadlines, js = _deadlines()

    await deadlines.arm(HumanInTheLoop.confirmation.invoke("Go?"), THREAD, _RunContext())

    assert js.published == []


@pytest.mark.asyncio
async def test_the_timeout_is_scheduled_onto_the_asking_run():
    deadlines, js = _deadlines()
    request = AgentInTheLoop.invoke(
        agent_class="RAGAgent", agent_id="rag", start_event=StartEvent(), timeout_seconds=30
    )

    await deadlines.arm(request, THREAD, _RunContext())

    [(subject, payload, headers)] = js.published
    assert subject == f"agent_deadline.LoopAgent.{request.event_id}"
    assert headers["Nats-Schedule"].startswith("@at ")
    assert headers["Nats-Schedule-Target"].startswith(
        "agent.LoopAgent.loop.thread.display.run.control_event.AgentInTheLoopTimeoutEvent."
    )
    assert json.loads(payload)["request_event_id"] == request.event_id


@pytest.mark.asyncio
async def test_the_first_answer_wins_and_cancels_the_timeout():
    deadlines, js = _deadlines()
    run_context = _RunContext()
    request = HumanInTheLoop.confirmation.invoke("Go?", timeout_seconds=60)
    await deadlines.arm(request, THREAD, run_context)
    answer = HumanInTheLoopConfirmationResponseEvent(response=True, request_event=request)

    assert await deadlines.settles(answer, run_context)
    assert await deadlines.settles(request.timed_out(), run_context) is False
    assert js.purged == [("agent_LoopAgent_stream", f"agent_deadline.LoopAgent.{request.event_id}")]


@pytest.mark.asyncio
async def test_an_answer_after_the_timeout_is_dropped():
    deadlines, js = _deadlines()
    run_context = _RunContext()
    request = AgentInTheLoop.invoke(agent_class="RAGAgent", agent_id="rag", start_event=StartEvent(), timeout_seconds=5)
    await deadlines.arm(request, THREAD, run_context)

    assert await deadlines.settles(request.timed_out(), run_context)
    late = AgentInTheLoop.response(stop_event=StopEvent(), request_event_id=request.event_id)
    assert await deadlines.settles(late, run_context) is False
    assert js.purged == []


@pytest.mark.asyncio
async def test_answers_to_requests_without_a_deadline_pass_as_before():
    """Untimed requests are never tracked, so a second answer, as a fan-out redelivery produces, still arrives."""
    deadlines, _ = _deadlines()
    run_context = _RunContext()
    answer = AgentInTheLoop.response(stop_event=StopEvent(), request_event_id="untimed")

    assert await deadlines.settles(answer, run_context)
    assert await deadlines.settles(answer, run_context)
    assert await deadlines.settles(StopEvent(), run_context)
