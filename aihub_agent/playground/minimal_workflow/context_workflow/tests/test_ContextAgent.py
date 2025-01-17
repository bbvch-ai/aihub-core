import pytest
from aihub_lib.nats.events import StartEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import scenarios, given, when, then, parsers
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.context_workflow.ContextAgent import ContextAgent
from playground.minimal_workflow.context_workflow.ContextAgentConfig import (
    ContextAgentConfig,
)
from playground.minimal_workflow.context_workflow.events.CustomStartEvent import (
    CustomStartEvent,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.asyncio_utils.bdd import async_test

scenarios("features/context_agent.feature")


SHARED_LIST = []


@given("a ContextAgent test runner", target_fixture="test_runner")
def _():
    return AgentTestRunner(
        agent_type=ContextAgent,
        agent_config=ContextAgentConfig(
            agent_id="context_agent",
            name=LocaleString(en="Context Agent"),
            description=LocaleString(
                en="This is an agent that accesses the run and thread context"
            ),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )


@when(parsers.parse('a the start event is sent with payload "{payload}"'))
@async_test
async def _(test_runner: AgentTestRunner, payload: str):
    async with test_runner.test_run() as topic:
        await test_runner.send_event_from_topic(
            start_event=StartEvent(
                messages=[ChatMessage(content=payload, role=MessageRole.USER)]
            ),
            topic=topic,
        )


@when(parsers.parse("'{number_of_runs:d}' runs are executed with distinct RunContexts"))
@async_test
async def execute_multiple_runs(test_runner: AgentTestRunner, number_of_runs: int):
    async with test_runner.test_run() as topic:

        for i in range(number_of_runs):
            start_event = CustomStartEvent(payload=f"Run {i + 1}")
            result = await test_runner.send_event_from_topic(
                topic=topic, start_event=start_event
            )
            print(SHARED_LIST)
            SHARED_LIST.append(result)


@then(
    parsers.parse("the thread context count should increment to '{expected_count:d}'")
)
@async_test
async def verify_thread_context_count(
    test_runner: AgentTestRunner, expected_count: int
):
    thread_context = await test_runner.get_thread_context()
    thread_count = await thread_context.get("count", 0)

    assert thread_count == expected_count, (
        f"Expected thread context count to be {expected_count}, "
        f"but got {thread_count}"
    )


@then(parsers.parse("each RunContext count should be '{expected_count:d}'"))
@async_test
async def verify_run_context_count(test_runner: AgentTestRunner, expected_count: int):

    for i, result in enumerate(SHARED_LIST):
        run_context = await test_runner.get_run_context(result.run_id)
        run_count = await run_context.get("count", 0)
        assert run_count == expected_count, (
            f"Expected RunContext count for run {i + 1} to be {expected_count}, "
            f"but got {run_count}"
        )


@then("RunContext values should remain isolated across runs")
@async_test
async def verify_run_context_isolation(test_runner: AgentTestRunner):

    run_counts = []
    for result in SHARED_LIST:
        run_context = await test_runner.get_run_context(result.run_id)
        run_counts.append(await run_context.get("count", 0))

    assert len(set(run_counts)) == len(
        run_counts
    ), "RunContext values are not isolated across runs."
