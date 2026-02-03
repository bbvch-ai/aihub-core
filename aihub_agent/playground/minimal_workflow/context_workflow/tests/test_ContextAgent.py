from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.asyncio_utils.bdd import async_test
from bson import ObjectId
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.context_workflow.ContextAgent import ContextAgent
from playground.minimal_workflow.context_workflow.ContextAgentConfig import (
    ContextAgentConfig,
)
from playground.minimal_workflow.context_workflow.events.ContextEvent import ContextEvent
from playground.minimal_workflow.context_workflow.events.CustomStartEvent import CustomStartEvent

scenarios("features/context_agent.feature")


@given("a ContextAgent test runner", target_fixture="test_runner")
def _():
    return AgentTestRunner(
        agent_type=ContextAgent,
        agent_config=ContextAgentConfig(
            agent_id="context_agent",
            agent_class=ContextAgent.__name__,
            name=LocaleString(en="Context Agent"),
            description=LocaleString(en="This is an agent that accesses the run and thread context"),
        ),
    )


@when(parsers.parse('two start events are sent with payload "{payload1}" and "{payload2}" for the same thread'))
@async_test
async def _(test_runner: AgentTestRunner, payload1: str, payload2: str):
    thread_id = str(ObjectId())
    async with test_runner.test_run(thread_id=thread_id) as topic:
        await test_runner.send_event_from_topic(
            start_event=CustomStartEvent(
                payload=payload1,
            ),
            topic=topic,
        )
    async with test_runner.test_run(thread_id=thread_id) as topic:
        await test_runner.send_event_from_topic(
            start_event=CustomStartEvent(
                payload=payload2,
            ),
            topic=topic,
        )


@then(
    parsers.parse(
        "the thread context count should increment to either '{expected_count_1:d}' or '{expected_count_2:d}'"
    )
)
@async_test
async def verify_thread_context_count(test_runner: AgentTestRunner, expected_count_1: int, expected_count_2: int):
    thread_counts = [event.thread_count for event in test_runner.get_events_of_class(ContextEvent)]
    assert expected_count_1 in thread_counts, f"Expected {expected_count_1} was not found in {thread_counts}"
    assert expected_count_2 in thread_counts, f"Expected {expected_count_2} was not found in {thread_counts}"
    assert len(thread_counts) == 2, f"Expected {thread_counts} to contain 2 values"


@then(parsers.parse("each RunContext count should be '{expected_count:d}'"))
@async_test
async def verify_run_context_count(test_runner: AgentTestRunner, expected_count: int):
    run_counts = [event.run_count for event in test_runner.get_events_of_class(ContextEvent)]
    for count in run_counts:
        assert count == expected_count, f"Expected {expected_count} was not found in {run_counts}"
    assert len(run_counts) == 2, f"Expected {run_counts} to contain 2 values"
