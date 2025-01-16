from unittest.mock import patch
from pytest_bdd import scenarios, given, when, then
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, StopEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from playground.minimal_workflow.conditional_workflow.events.EventA import EventA
from playground.minimal_workflow.conditional_workflow.events.EventB import EventB
from playground.minimal_workflow.conditional_workflow.ConditionalAgent import (
    ConditionalAgent,
)
from playground.minimal_workflow.conditional_workflow.ConditionalAgentConfig import (
    ConditionalAgentConfig,
)

scenarios("../tests/features/configured_agent.feature")


@given("a ConditionalAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=ConditionalAgent,
        agent_config=ConditionalAgentConfig(
            agent_id="conditional_agent",
            name=LocaleString(en="Conditional Agent"),
            description=LocaleString(en="This is a conditional agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )


@when("the start event is sent and random is forced to produce EventA")
@async_test
async def _(agent_runner: AgentTestRunner):
    with patch("random.random", return_value=0.6):  # Force EventA (random > 0.5)
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(
                start_event=StartEvent(),
                topic=topic,
            )


@when("the start event is sent and random is forced to produce EventB")
@async_test
async def _(agent_runner: AgentTestRunner):
    with patch("random.random", return_value=0.4):  # Force EventB (random <= 0.5)
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(
                start_event=StartEvent(),
                topic=topic,
            )


@then("an EventA event is present")
def _(agent_runner: AgentTestRunner):
    event = agent_runner.get_event_of_type(EventA)
    assert event is not None, "EventA was not received"


@then("an EventB event is present")
def _(agent_runner: AgentTestRunner):
    event = agent_runner.get_event_of_type(EventB)
    assert event is not None, "EventB was not received"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "StopEvent was not received"
