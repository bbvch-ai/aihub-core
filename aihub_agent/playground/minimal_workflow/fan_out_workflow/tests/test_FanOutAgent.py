from pytest_bdd import scenarios, given, when, then
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, StopEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from playground.minimal_workflow.fan_out_workflow.events.EventA import EventA
from playground.minimal_workflow.fan_out_workflow.events.EventB import EventB
from playground.minimal_workflow.fan_out_workflow.FanOutAgent import FanOutAgent
from playground.minimal_workflow.fan_out_workflow.FanOutAgentConfig import (
    FanOutAgentConfig,
)

scenarios("../tests/features/fan_out_agent.feature")


@given("a FanOutAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=FanOutAgent,
        agent_config=FanOutAgentConfig(
            agent_id="fan_out_agent",
            name=LocaleString(en="Fan Out Agent"),
            description=LocaleString(en="This agent demonstrates fan-out processing"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )


@when("the start event is sent")
@async_test
async def _(agent_runner: AgentTestRunner):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            start_event=StartEvent(messages=[]),
            topic=topic,
        )


@then("5 EventA events are present")
def _(agent_runner: AgentTestRunner):
    events = agent_runner.get_events_of_type(EventA)
    assert len(events) == 5, f"Expected 5 EventA events but found {len(events)}"


@then("5 EventB events are present")
def _(agent_runner: AgentTestRunner):
    events = agent_runner.get_events_of_type(EventB)
    assert len(events) == 5, f"Expected 5 EventB events but found {len(events)}"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "StopEvent was not received"
