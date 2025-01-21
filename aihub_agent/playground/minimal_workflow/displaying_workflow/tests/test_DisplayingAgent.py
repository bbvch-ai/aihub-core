from pytest_bdd import scenarios, given, when, then
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, ThoughtEvent, ChunkEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from playground.minimal_workflow.displaying_workflow.DisplayingAgent import (
    DisplayingAgent,
)
from playground.minimal_workflow.displaying_workflow.DisplayingAgentConfig import (
    DisplayingAgentConfig,
)

scenarios("../tests/features/displaying_agent.feature")


@given("a DisplayingAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=DisplayingAgent,
        agent_config=DisplayingAgentConfig(
            agent_id="displaying_agent",
            name=LocaleString(en="Displaying Agent"),
            description=LocaleString(en="This is an agent that displays events"),
            system_prompt=LocaleString(en="You are an agent that displays events."),
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


@then("a StartEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_start_event, "StartEvent was not received"


@then("a ThoughtEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_type(ThoughtEvent), "ThoughtEvent was not received"


@then("a ChunkEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_type(ChunkEvent), "ChunkEvent was not received"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "StopEvent was not received"
