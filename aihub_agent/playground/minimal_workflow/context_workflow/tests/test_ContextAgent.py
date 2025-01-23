import pytest
import pytest_asyncio
from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.workflow import StartEvent
from pytest_bdd import scenarios, given, when, then, parsers

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StopEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from playground.minimal_workflow.context_workflow.ContextAgent import ContextAgent
from playground.minimal_workflow.context_workflow.ContextAgentConfig import (
    ContextAgentConfig,
)
from playground.minimal_workflow.context_workflow.events.CustomStartEvent import CustomStartEvent
from playground.minimal_workflow.context_workflow.events.ContextEvent import ContextEvent

scenarios("features/context_agent.feature")


@pytest_asyncio.fixture
async def test_runner():
    """Returns an AgentTestRunner configured for the MultistepHumanInTheLoopAgent."""
    test_runner = AgentTestRunner(
        agent_type=ContextAgent,
        agent_config=ContextAgentConfig(
            agent_id="context_agent",
            name=LocaleString(en="Context Agent"),
            description=LocaleString(en="This is an agent that accesses the run and thread context"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )
    await test_runner.test_run_start()
    yield test_runner
    await test_runner.test_run_stop()


@given(parsers.parse('a ContextAgent is started with the payload "{payload}"'))
@pytest.mark.asyncio
async def start_agent(test_runner: AgentTestRunner, payload: str):
    await test_runner.send_event_from_topic(start_event=CustomStartEvent(payload=payload), topic=test_runner.topic)


@given(parsers.parse('another ContextAgent is started with the payload "{payload}"'))
@pytest.mark.asyncio
async def start_agent(test_runner: AgentTestRunner, payload: str):
    topic = test_runner.topic.model_copy()
    topic.run_id = str(ObjectId())
    await test_runner.send_event_from_topic(start_event=CustomStartEvent(payload=payload), topic=topic)


@when("the agent successfully started")
@pytest.mark.asyncio
async def start_agent(test_runner: AgentTestRunner):
    await test_runner.wait_for_event(CustomStartEvent)


@when(parsers.parse('the thread context count is "{count:d}"'))
@pytest.mark.asyncio
async def thread_count(test_runner: AgentTestRunner, count: int):
    event = await test_runner.wait_for_event(ContextEvent)
    assert event.thread_count == count


@when(parsers.parse('the run context count is "{count:d}"'))
@pytest.mark.asyncio
async def run_count(test_runner: AgentTestRunner, count: int):
    event = await test_runner.wait_for_event(ContextEvent)
    assert event.run_count == count


@then(parsers.parse('a ContextEvent is returned with thread count "{thread_count:d}" and run count "{run_count:d}"'))
@pytest.mark.asyncio
async def event_returned(test_runner: AgentTestRunner, thread_count: int, run_count: int):
    event = await test_runner.wait_for_event(ContextEvent)
    assert event.thread_count == thread_count
    assert event.run_count == run_count


@then("the agent stopped")
@pytest.mark.asyncio
async def assert_agent_stopped(test_runner: AgentTestRunner):
    await test_runner.wait_for_event(StopEvent)
    assert test_runner.has_stop_event
