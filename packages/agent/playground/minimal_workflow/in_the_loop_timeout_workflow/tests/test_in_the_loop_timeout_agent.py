"""A question nobody answers ends in its timeout event, delivered by NATS at the deadline, and the run continues."""

import pytest
from swiss_ai_hub.core.events.agent import (
    HumanInTheLoopConfirmation,
    HumanInTheLoopConfirmationRequestEvent,
    HumanInTheLoopTimeoutEvent,
    StartEvent,
    StopEvent,
)
from swiss_ai_hub.core.i18n import LocaleString

from playground.minimal_workflow.in_the_loop_timeout_workflow.in_the_loop_timeout_agent import InTheLoopTimeoutAgent
from playground.minimal_workflow.in_the_loop_timeout_workflow.in_the_loop_timeout_agent_config import (
    InTheLoopTimeoutAgentConfig,
)
from playground.minimal_workflow.in_the_loop_timeout_workflow.question_settled_event import QuestionSettledEvent
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner


def _runner() -> AgentTestRunner:
    return AgentTestRunner(
        agent_type=InTheLoopTimeoutAgent,
        agent_config=InTheLoopTimeoutAgentConfig(
            agent_id="in_the_loop_timeout_agent",
            agent_class=InTheLoopTimeoutAgent.__name__,
            name=LocaleString(en="In The Loop Timeout Agent"),
            description=LocaleString(en="Falls back when a question goes unanswered"),
        ),
    )


@pytest.mark.asyncio
async def test_an_unanswered_question_takes_the_fallback():
    runner = _runner()
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(start_event=StartEvent(), topic=topic)
        await runner.wait_for_event(HumanInTheLoopTimeoutEvent, timeout=30)
        settled = await runner.wait_for_event(QuestionSettledEvent)
        await runner.wait_for_event(StopEvent)

    assert settled.outcome.startswith("no answer within 2s")


@pytest.mark.asyncio
async def test_an_answer_in_time_wins_and_the_timeout_never_arrives():
    runner = _runner()
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(start_event=StartEvent(), topic=topic)
        request = await runner.wait_for_event(HumanInTheLoopConfirmationRequestEvent)
        await runner.send_event_from_topic(
            start_event=HumanInTheLoopConfirmation.response(response=True, request_event=request),
            topic=request.topic,
        )
        settled = await runner.wait_for_event(QuestionSettledEvent)
        await runner.wait_for_event(StopEvent)

    assert settled.outcome == "confirmed"
    assert not runner.has_event_of_class(HumanInTheLoopTimeoutEvent)
