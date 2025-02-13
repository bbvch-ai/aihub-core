import pytest
import pytest_asyncio
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, StopEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import scenarios, given, when, then, parsers

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.MultistepHumanInTheLoopAgent import (
    MultistepHumanInTheLoopAgent,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.MultistepHumanInTheLoopAgentConfig import (
    MultistepHumanInTheLoopAgentConfig,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.FirstStepHumanInTheLoop import (
    FirstStepHumanInTheLoopRequestEvent,
    FirstStepHumanInTheLoopResponseEvent,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.SecondStepHumanInTheLoop import (
    SecondStepHumanInTheLoopRequestEvent,
    SecondStepHumanInTheLoopResponseEvent,
)

# Link this test file to your .feature file:
scenarios("../tests/features/multistep_human_in_the_loop_agent.feature")


@pytest_asyncio.fixture
async def agent_runner():
    """Returns an AgentTestRunner configured for the MultistepHumanInTheLoopAgent."""
    agent_runner = AgentTestRunner(
        agent_type=MultistepHumanInTheLoopAgent,
        agent_config=MultistepHumanInTheLoopAgentConfig(
            agent_id="multistep_human_in_the_loop_agent",
            name=LocaleString(en="Multistep Human In The Loop Agent"),
            description=LocaleString(en="This is a multistep human in the loop agent"),
            system_prompt=LocaleString(en="You are a multistep agent"),
        ),
    )
    await agent_runner.test_run_start()
    yield agent_runner
    await agent_runner.test_run_stop()


@given("a MultistepHumanInTheLoopAgent is started")
@pytest.mark.asyncio
async def start_agent(agent_runner: AgentTestRunner):
    await agent_runner.send_event_from_topic(
        start_event=StartEvent(messages=[ChatMessage(role=MessageRole.USER)]), topic=agent_runner.topic
    )


@when("the agent successfully started")
@pytest.mark.asyncio
async def start_agent(agent_runner: AgentTestRunner):
    await agent_runner.wait_for_event(StartEvent)


@then(parsers.parse('the agent initiated the first HITL-step with the question "{text}"'))
@pytest.mark.asyncio
async def assert_first_step_initiated(agent_runner: AgentTestRunner, text: str):
    event = await agent_runner.wait_for_event(FirstStepHumanInTheLoopRequestEvent)
    assert event.question == text, f"Expected question '{text}', but got '{event.question}'."


@when(parsers.parse('the first HITL-step is answered with "{text}"'))
@pytest.mark.asyncio
async def answer_first_step(agent_runner: AgentTestRunner, text: str):
    event = await agent_runner.wait_for_event(FirstStepHumanInTheLoopRequestEvent)
    await agent_runner.send_event_from_topic(
        start_event=FirstStepHumanInTheLoopResponseEvent(response=text, request_event=event),
        topic=event.topic,
    )


@then(parsers.parse('the agent initiated the second HITL-step with the question "{text}"'))
@pytest.mark.asyncio
async def assert_second_step_initiated(agent_runner: AgentTestRunner, text: str):
    event = await agent_runner.wait_for_event(FirstStepHumanInTheLoopResponseEvent)
    assert event.question == text, f"Expected question '{text}', but got '{event.request_event.question}'."


@when(parsers.parse('the second HITL-step is answered with "{text}"'))
@pytest.mark.asyncio
async def answer_second_step(agent_runner: AgentTestRunner, text: str):
    event = await agent_runner.wait_for_event(SecondStepHumanInTheLoopRequestEvent)
    await agent_runner.send_event_from_topic(
        start_event=SecondStepHumanInTheLoopResponseEvent(response=text, request_event=event),
        topic=event.topic,
    )


@then("the agent stopped")
@pytest.mark.asyncio
async def assert_agent_stopped(agent_runner: AgentTestRunner):
    await agent_runner.wait_for_event(StopEvent)
    assert agent_runner.has_stop_event
