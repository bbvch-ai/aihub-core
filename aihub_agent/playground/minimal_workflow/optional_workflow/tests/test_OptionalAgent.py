# tests/test_optional_agent.py

from unittest.mock import patch

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from pytest_bdd import given, scenarios, then, when

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.optional_workflow.events.EventOptionalA import EventOptionalA
from playground.minimal_workflow.optional_workflow.events.EventOptionalB import EventOptionalB
from playground.minimal_workflow.optional_workflow.events.EventOptionalC import EventOptionalC
from playground.minimal_workflow.optional_workflow.events.EventOptionalD import EventOptionalD
from playground.minimal_workflow.optional_workflow.OptionalAgent import OptionalAgent
from playground.minimal_workflow.optional_workflow.OptionalAgentConfig import (
    OptionalAgentConfig,
)

# Load scenarios from your feature file
scenarios("./features/optional_agent.feature")


@given("an OptionalAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=OptionalAgent,
        agent_config=OptionalAgentConfig(
            agent_id="optional_agent",
            name=LocaleString(en="Optional Agent"),
            description=LocaleString(en="This is an optional agent"),
        ),
    )


@when("the start event is sent and random is forced to produce only EventA")
@async_test
async def _(agent_runner: AgentTestRunner):
    """
    Forces the random number to be > 0.5 so that only EventA is produced.
    """
    with patch("random.random", return_value=0.6):
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(
                start_event=StartEvent(),
                topic=topic,
            )


@when("the start event is sent and random is forced to produce EventA and EventB")
@async_test
async def _(agent_runner: AgentTestRunner):
    """
    Forces the random number to be <= 0.5 so that EventA and EventB are produced.
    """
    with patch("random.random", return_value=0.4):
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(
                start_event=StartEvent(),
                topic=topic,
            )


@then("an EventA event is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(EventOptionalA), "EventA was not received"


@then("an EventB event is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(EventOptionalB), "EventB was not received"


@then("no EventB event is present")
def _(agent_runner: AgentTestRunner):
    assert not agent_runner.has_event_of_class(EventOptionalB), "EventB was received"


@then("an EventC event is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(EventOptionalC), "EventC was not received"


@then("no EventC event is present")
def _(agent_runner: AgentTestRunner):
    assert not agent_runner.has_event_of_class(EventOptionalC), "EventC was received"


@then("an EventD event is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(EventOptionalD), "EventD was not received"


@then("no EventD event is present")
def _(agent_runner: AgentTestRunner):
    assert not agent_runner.has_event_of_class(EventOptionalD), "EventD was received"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "StopEvent was not received"
