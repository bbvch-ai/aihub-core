from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.events.agent import StartEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test

from playground.minimal_workflow.precondition_workflow.events.parallel_event import ParallelEvent
from playground.minimal_workflow.precondition_workflow.precondition_agent import PreconditionAgent
from playground.minimal_workflow.precondition_workflow.precondition_agent_config import PreconditionAgentConfig
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

scenarios("./features/precondition_agent.feature")


@given(parsers.parse("a PreconditionAgent runner with {number_of_events:d} events"), target_fixture="agent_runner")
def _(number_of_events):
    return AgentTestRunner(
        agent_type=PreconditionAgent,
        agent_config=PreconditionAgentConfig(
            agent_id="precondition_agent",
            agent_class=PreconditionAgent.__name__,
            name=LocaleString(en="Agent with preconditions"),
            description=LocaleString(en="This is an agent that has preconditions"),
            number_of_events=number_of_events,
        ),
    )


@when("the start event is sent")
@async_test
async def _(agent_runner: AgentTestRunner):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            start_event=StartEvent(),
            topic=topic,
        )


@then(parsers.parse('5 ParallelEvent events with payloads "{payloads}" are present'))
def verify_parallel_events_payloads(agent_runner: AgentTestRunner, payloads: str):
    expected_payloads = payloads.split(",")
    events = agent_runner.get_events_of_class(ParallelEvent)
    actual_payloads = [event.payload for event in events]
    assert len(events) == 5, f"Expected 5 ParallelEvent events but found {len(events)}"
    assert sorted(actual_payloads) == sorted(expected_payloads), (
        f"Expected ParallelEvent payloads {expected_payloads} but found {actual_payloads}"
    )


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "StopEvent was not received"
