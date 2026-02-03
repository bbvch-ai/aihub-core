from unittest.mock import patch

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.conditional_workflow.ConditionalAgent import (
    ConditionalAgent,
)
from playground.minimal_workflow.conditional_workflow.ConditionalAgentConfig import (
    ConditionalAgentConfig,
)
from playground.minimal_workflow.conditional_workflow.events.AboveThresholdEvent import AboveThresholdEvent
from playground.minimal_workflow.conditional_workflow.events.BelowThresholdEvent import BelowThresholdEvent

scenarios("features/conditional_agent.feature")


@given("a ConditionalAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=ConditionalAgent,
        agent_config=ConditionalAgentConfig(
            agent_id="conditional_agent",
            agent_class=ConditionalAgent.__name__,
            name=LocaleString(en="Conditional Agent"),
            description=LocaleString(en="This is a conditional agent"),
        ),
    )


@when(parsers.parse("the start event is sent and the random value is {value}"), converters={"value": float})
@async_test
async def _(value: float, agent_runner: AgentTestRunner):
    with patch("random.random", return_value=value):
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(
                start_event=StartEvent(),
                topic=topic,
            )


@then("the agent processes the branch for values greater than 0.5")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(AboveThresholdEvent), "AboveThresholdEvent was not received"
    assert not agent_runner.has_event_of_class(BelowThresholdEvent), "BelowThresholdEvent was received"


@then("the agent processes the branch for values less than or equal to 0.5")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(BelowThresholdEvent), "BelowThresholdEvent was not received"
    assert not agent_runner.has_event_of_class(AboveThresholdEvent), "AboveThresholdEvent was received"


@then("the workflow completes successfully")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "StopEvent was not received"
