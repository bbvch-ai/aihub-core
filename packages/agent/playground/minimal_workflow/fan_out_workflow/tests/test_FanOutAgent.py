from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.events.agent import StartEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test

from playground.minimal_workflow.fan_out_workflow.events.FanOutA import FanOutA
from playground.minimal_workflow.fan_out_workflow.events.FanOutB import FanOutB
from playground.minimal_workflow.fan_out_workflow.FanOutAgent import FanOutAgent
from playground.minimal_workflow.fan_out_workflow.FanOutAgentConfig import (
    FanOutAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

scenarios("./features/fan_out_agent.feature")


@given("a FanOutAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=FanOutAgent,
        agent_config=FanOutAgentConfig(
            agent_id="fan_out_agent",
            name=LocaleString(en="Fan Out Agent"),
            description=LocaleString(en="This agent demonstrates fan-out processing"),
        ),
    )


@when("the start event is sent")
@async_test
async def _(agent_runner: AgentTestRunner):
    async with agent_runner.test_run(delay_before_stop=10) as topic:
        await agent_runner.send_event_from_topic(
            start_event=StartEvent(),
            topic=topic,
        )


@then(parsers.parse('5 EventA events with payloads "{payloads}" are present'))
def verify_event_a_payloads(agent_runner: AgentTestRunner, payloads: str):
    expected_payloads = payloads.split(",")
    events = agent_runner.get_events_of_class(FanOutA)
    actual_payloads = [event.payload for event in events]
    assert len(events) == 5, f"Expected 5 EventA events but found {len(events)}"
    assert sorted(actual_payloads) == sorted(expected_payloads), (
        f"Expected EventA payloads {expected_payloads} but found {actual_payloads}"
    )


@then(parsers.parse('5 EventB events with matching payloads "{payloads}" are present'))
def verify_event_b_payloads(agent_runner: AgentTestRunner, payloads: str):
    expected_payloads = payloads.split(",")
    events_b = agent_runner.get_events_of_class(FanOutB)
    actual_payloads = [event.payload for event in events_b]
    assert len(events_b) == 5, f"Expected 5 EventB events but found {len(events_b)}"
    assert sorted(actual_payloads) == sorted(expected_payloads), (
        f"Expected EventB payloads {expected_payloads} but found {actual_payloads}"
    )


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "StopEvent was not received"
