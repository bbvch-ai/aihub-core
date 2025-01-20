from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import scenarios, given, when, then, parsers

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from playground.minimal_workflow.simple_workflow.SimpleAgent import SimpleAgent
from playground.minimal_workflow.simple_workflow.SimpleAgentConfig import SimpleAgentConfig
from playground.minimal_workflow.simple_workflow.events.EventA import EventA

scenarios("../tests/features/simple_agent.feature")


@given("a SemanticEventAgent runner", target_fixture="agent_runner")
def agent_runner():
    return AgentTestRunner(
        agent_type=SimpleAgent,
        agent_config=SimpleAgentConfig(
            agent_id="simple_agent",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )


@when("a the start event is sent")
@async_test
async def test_start(agent_runner: AgentTestRunner):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            start_event=StartEvent(messages=[]),
            topic=topic,
        )


@then("a StartEvent is present")
def test_start_present(agent_runner: AgentTestRunner):
    assert agent_runner.has_start_event, "Agent did not receive start event"
