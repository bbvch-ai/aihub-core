from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.events.agent.user.UserMessageEvent import UserMessageEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

from playground.minimal_workflow.simple_workflow.events.SimpleEventA import SimpleEventA
from playground.minimal_workflow.simple_workflow.SimpleAgent import SimpleAgent
from playground.minimal_workflow.simple_workflow.SimpleAgentConfig import SimpleAgentConfig
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner

scenarios("./features/simple_agent.feature")


@given("a SimpleAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=SimpleAgent,
        agent_config=SimpleAgentConfig(
            agent_id="simple_agent",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
        ),
    )


@when(parsers.parse('a the start event is sent with payload "{payload}"'))
@async_test
async def _(agent_runner: AgentTestRunner, payload: str):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=payload, role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
            topic=topic,
        )


@then(parsers.parse('a StartEvent is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.has_start_event, "Agent did not receive start event"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not receive stop event"


@then(parsers.parse('an EventA event is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.get_event_of_class(SimpleEventA).payload == payload, "Agent received incorrect data"
