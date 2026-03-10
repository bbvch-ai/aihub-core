from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.control.start.StartEvent import StartEvent
from swiss_ai_hub.core.nats.events.display.ChunkEvent import ChunkEvent
from swiss_ai_hub.core.nats.events.display.ThoughtEvent import ThoughtEvent
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

from playground.minimal_workflow.displaying_workflow.DisplayingAgent import (
    DisplayingAgent,
)
from playground.minimal_workflow.displaying_workflow.DisplayingAgentConfig import (
    DisplayingAgentConfig,
)
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner

scenarios("./features/displaying_agent.feature")


@given("a DisplayingAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=DisplayingAgent,
        agent_config=DisplayingAgentConfig(
            agent_id="displaying_agent",
            name=LocaleString(en="Displaying Agent"),
            description=LocaleString(en="This is an agent that displays events"),
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


@then(parsers.parse('a ThoughtEvent with content "{thought_content}" is present'))
def _(agent_runner: AgentTestRunner, thought_content: str):
    assert agent_runner.has_event_of_class(ThoughtEvent), "ThoughtEvent was not received"
    assert agent_runner.get_event_of_class(ThoughtEvent, exact=True).reasoning_content.strip() == thought_content


@then(parsers.parse('a ChunkEvent with content "{chunk_content}" is present'))
def _(agent_runner: AgentTestRunner, chunk_content: str):
    assert agent_runner.has_event_of_class(ChunkEvent), "ChunkEvent was not received"
    assert agent_runner.get_event_of_class(ChunkEvent, exact=True).content == chunk_content


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "StopEvent was not received"
