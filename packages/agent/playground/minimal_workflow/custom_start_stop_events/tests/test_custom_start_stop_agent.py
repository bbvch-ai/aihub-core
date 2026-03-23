from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test

from playground.minimal_workflow.custom_start_stop_events.custom_start_stop_event_agent import CustomStartStopEventAgent
from playground.minimal_workflow.custom_start_stop_events.custom_start_stop_event_agent_config import (
    CustomStartStopEventAgentConfig,
)
from playground.minimal_workflow.custom_start_stop_events.events.my_custom_start_event import (
    MyCustomStartEvent,
    PydanticPayload,
)
from playground.minimal_workflow.custom_start_stop_events.events.my_custom_stop_event import MyCustomStopEvent
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

scenarios("./features/custom_start_stop_agent.feature")


@given("a CustomStartStopEventAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=CustomStartStopEventAgent,
        agent_config=CustomStartStopEventAgentConfig(
            agent_id="custom_start_stop_agent",
            agent_class=CustomStartStopEventAgent.__name__,
            name=LocaleString(en="Custom Start Stop Agent"),
            description=LocaleString(en="This is a very custom agent"),
        ),
    )


@when(parsers.parse('a the custom start event is sent with payload "{payload}"'))
@async_test
async def _(agent_runner: AgentTestRunner, payload: str):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            start_event=MyCustomStartEvent(
                payload=PydanticPayload(payload=payload),
            ),
            topic=topic,
        )


@then(parsers.parse('a MyCustomStartEvent is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.has_start_event, "Agent did not receive start event"


@then(parsers.parse('an MyCustomStopEvent event is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.get_event_of_class(MyCustomStopEvent).payload.payload == payload, (
        "Agent received incorrect data"
    )
