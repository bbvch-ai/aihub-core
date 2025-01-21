from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import scenarios, given, when, then, parsers

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test

from playground.minimal_workflow.multi_locale_workflow.MultiLocaleAgent import MultiLocaleAgent
from playground.minimal_workflow.multi_locale_workflow.MultiLocaleAgentConfig import MultiLocaleAgentConfig
from playground.minimal_workflow.multi_locale_workflow.events.EventA import EventA

scenarios("../tests/features/multi_locale_agent.feature")


@given("a MultiLocaleAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=MultiLocaleAgent,
        agent_config=MultiLocaleAgentConfig(
            agent_id="simple_agent",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )


@when(parsers.parse('a StartEvent is sent with locale "{locale}"'))
@async_test
async def _(agent_runner: AgentTestRunner, locale: str):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            start_event=StartEvent(
                locale=locale,
                messages=[ChatMessage(content="Hello", role=MessageRole.USER)],
            ),
            topic=topic,
        )


@then(parsers.parse('a StartEvent is present with locale "{locale}"'))
def _(agent_runner: AgentTestRunner, locale: str):
    assert agent_runner.has_start_event, "Agent did not receive start event"
    assert (
        agent_runner.get_event_of_type(StartEvent).locale == locale
    ), "Start event locale does not match expected locale"


@then(parsers.parse('a EventA is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.has_start_event, "Agent did not receive start event"
    assert agent_runner.get_event_of_type(EventA).payload == payload, "Agent has wrong payload"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not receive stop event"
