import pytest
import pytest_asyncio
from swiss_ai_hub.core.events.agent.control.start.StartEvent import StartEvent
from swiss_ai_hub.core.events.agent.control.stop.StopEvent import StopEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString

from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.FirstStepHumanInTheLoop import (
    FirstStepHumanInTheLoopRequestEvent,
    FirstStepHumanInTheLoopResponseEvent,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.SecondStepHumanInTheLoop import (
    SecondStepHumanInTheLoopRequestEvent,
    SecondStepHumanInTheLoopResponseEvent,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.MultistepHumanInTheLoopAgent import (
    MultistepHumanInTheLoopAgent,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.MultistepHumanInTheLoopAgentConfig import (
    MultistepHumanInTheLoopAgentConfig,
)
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner


@pytest_asyncio.fixture
async def agent_runner():
    """Returns an AgentTestRunner configured for the MultistepHumanInTheLoopAgent."""
    agent_runner = AgentTestRunner(
        agent_type=MultistepHumanInTheLoopAgent,
        agent_config=MultistepHumanInTheLoopAgentConfig(
            agent_id="multistep_human_in_the_loop_agent",
            agent_class=MultistepHumanInTheLoopAgent.__name__,
            name=LocaleString(en="Multistep Human In The Loop Agent"),
            description=LocaleString(en="This is a multistep human in the loop agent"),
        ),
    )
    await agent_runner.test_run_start()
    yield agent_runner
    await agent_runner.test_run_stop()


@pytest.mark.asyncio
async def test_multistep_human_in_the_loop_workflow(agent_runner: AgentTestRunner):
    # Start the agent
    await agent_runner.send_event_from_topic(start_event=StartEvent(), topic=agent_runner.topic)

    # Wait for the first step
    event = await agent_runner.wait_for_event(FirstStepHumanInTheLoopRequestEvent)

    # Assert the first step
    assert event.question == "Shall I continue?", f"Expected question 'Shall I continue?', but got '{event.question}'."

    # Answer the first step
    await agent_runner.send_event_from_topic(
        start_event=FirstStepHumanInTheLoopResponseEvent(response="Yes", request_event=event), topic=event.topic
    )

    # Wait for the second step
    event = await agent_runner.wait_for_event(SecondStepHumanInTheLoopRequestEvent)

    # Assert the second step
    assert event.question == "Are you sure?", f"Expected question 'Are you sure?', but got '{event.question}'."

    # Answer the second step
    await agent_runner.send_event_from_topic(
        start_event=SecondStepHumanInTheLoopResponseEvent(response="Yes", request_event=event), topic=event.topic
    )

    # Wait for the agent to stop
    await agent_runner.wait_for_event(StopEvent)

    # Assert the agent has stopped
    assert agent_runner.has_stop_event
