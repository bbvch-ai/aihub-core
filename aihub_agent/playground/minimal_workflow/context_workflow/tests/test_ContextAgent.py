from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import scenarios, given, when, then, parsers

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.context_workflow.ContextAgent import ContextAgent
from playground.minimal_workflow.context_workflow.ContextAgentConfig import (
    ContextAgentConfig,
)
from playground.minimal_workflow.context_workflow.events.CustomStartEvent import CustomStartEvent
from playground.minimal_workflow.context_workflow.events.EventA import EventA

scenarios("features/context_agent.feature")

SHARED_LIST = []


@given("a ContextAgent test runner", target_fixture="test_runner")
def _():
    return AgentTestRunner(
        agent_type=ContextAgent,
        agent_config=ContextAgentConfig(
            agent_id="context_agent",
            name=LocaleString(en="Context Agent"),
            description=LocaleString(en="This is an agent that accesses the run and thread context"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )


@when(parsers.parse('two start events are sent with payload "{payload1}" and "{payload2}" for the same thread'))
@async_test
async def _(test_runner: AgentTestRunner, payload1: str, payload2: str):
    thread_id = str(ObjectId())
    async with test_runner.test_run(thread_id=thread_id) as topic:
        await test_runner.send_event_from_topic(
            start_event=CustomStartEvent(payload=payload1),
            topic=topic,
        )
    async with test_runner.test_run(thread_id=thread_id) as topic:
        await test_runner.send_event_from_topic(
            start_event=CustomStartEvent(payload=payload2),
            topic=topic,
        )


@then(
    parsers.parse(
        "the thread context count should increment to either '{expected_count_1:d}' or '{expected_count_2:d}'"
    )
)
@async_test
async def verify_thread_context_count(test_runner: AgentTestRunner, expected_count_1: int, expected_count_2: int):
    thread_count = test_runner.get_event_of_type(EventA).thread_count
    assert (
        thread_count == expected_count_1 or thread_count == expected_count_2
    ), f"Expected thread context count to be either {expected_count_1} or {expected_count_2}, but got {thread_count}"


@then(parsers.parse("each RunContext count should be '{expected_count:d}'"))
@async_test
async def verify_run_context_count(test_runner: AgentTestRunner, expected_count: int):
    run_count = test_runner.get_event_of_type(EventA).run_count
    assert run_count == expected_count, f"Expected RunContext count to be {expected_count}, but got {run_count}"
