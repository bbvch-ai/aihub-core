from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events import StartEvent
from swiss_ai_hub.core.nats.events.human_in_the_loop import HumanInTheLoopInput
from swiss_ai_hub.core.nats.events.human_in_the_loop.request import HumanInTheLoopInputRequestEvent
from swiss_ai_hub.core.nats.events.human_in_the_loop.response import HumanInTheLoopInputResponseEvent
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

from playground.minimal_workflow.human_in_the_loop_workflow.HumanInTheLoopAgent import (
    HumanInTheLoopAgent,
)
from playground.minimal_workflow.human_in_the_loop_workflow.HumanInTheLoopAgentConfig import (
    HumanInTheLoopAgentConfig,
)
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner

# Link this test file to your .feature file:
scenarios("./features/human_in_the_loop_agent.feature")


@given("a HumanInTheLoopAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=HumanInTheLoopAgent,
        agent_config=HumanInTheLoopAgentConfig(
            agent_id="human_in_the_loop_agent",
            agent_class=HumanInTheLoopAgent.__name__,
            name=LocaleString(en="Human In The Loop Agent"),
            description=LocaleString(en="This is a very human in the loop agent"),
        ),
    )


@when(
    parsers.parse(
        'a start event is sent and a HumanInTheLoopResponseEvent event with the response "{response}" is sent'
    )
)
@async_test
async def _(agent_runner: AgentTestRunner, response: str):
    async with agent_runner.test_run() as topic:
        # Send StartEvent
        await agent_runner.send_event_from_topic(start_event=StartEvent(), topic=topic)
        # Get the HumanInTheLoopInputRequestEvent and send the corresponding response
        hil_request_event = await agent_runner.wait_for_event(HumanInTheLoopInputRequestEvent)
        await agent_runner.send_event_from_topic(
            start_event=HumanInTheLoopInput.response(response=response, request_event=hil_request_event),
            topic=hil_request_event.topic,
        )


@then("a StartEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_start_event, "Agent did not receive StartEvent"


@then("a HumanInTheLoopRequestEvent event is present")
def _(agent_runner: AgentTestRunner):
    # Make sure the agent emitted HumanInTheLoopInputRequestEvent
    assert agent_runner.has_event_of_class(HumanInTheLoopInputRequestEvent)


@then(parsers.parse('a HumanInTheLoopResponseEvent event with the response "{response}" is present'))
def _(agent_runner: AgentTestRunner, response: str):
    assert agent_runner.get_event_of_class(HumanInTheLoopInputResponseEvent).response == response, (
        "Agent did not receive correct response"
    )


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not receive StopEvent"
