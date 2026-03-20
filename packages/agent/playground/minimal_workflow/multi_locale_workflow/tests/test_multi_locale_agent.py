import os

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.auth import DangerousDevelopmentOnlyAuthSettings
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test

from playground.minimal_workflow.multi_locale_workflow.events.multi_locale_event import MultiLocaleEvent
from playground.minimal_workflow.multi_locale_workflow.multi_locale_agent import MultiLocaleAgent
from playground.minimal_workflow.multi_locale_workflow.multi_locale_agent_config import MultiLocaleAgentConfig
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

scenarios("./features/multi_locale_agent.feature")


@given(parsers.parse('a MultiLocaleAgent runner with locale_path "{locale_path}"'), target_fixture="agent_runner")
def _(locale_path: str):
    return AgentTestRunner(
        agent_type=MultiLocaleAgent,
        agent_config=MultiLocaleAgentConfig(
            agent_id="simple_agent",
            agent_class=MultiLocaleAgent.__name__,
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            locale_path=locale_path,
        ),
        locale_paths=[os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../translations"))],
    )


@when(parsers.parse('a StartEvent is sent with locale "{locale}"'))
@async_test
async def _(agent_runner: AgentTestRunner, locale: str):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            start_event=UserMessageEvent(
                locale=locale,
                messages=[ChatMessage(content="Hello", role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
            topic=topic,
        )


@then(parsers.parse('an event is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.has_start_event, "Agent did not receive start event"
    assert agent_runner.get_event_of_class(MultiLocaleEvent).payload == payload, "Agent has wrong payload"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not receive stop event"
