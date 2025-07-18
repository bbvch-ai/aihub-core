from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.asyncio_utils.bdd import async_test
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.custom_start_stop_events.CustomStartStopEventAgent import CustomStartStopEventAgent
from playground.minimal_workflow.custom_start_stop_events.CustomStartStopEventAgentConfig import (
    CustomStartStopEventAgentConfig,
)
from playground.minimal_workflow.custom_start_stop_events.events.MyCustomStartEvent import (
    MyCustomStartEvent,
    PydanticPayload,
)
from playground.minimal_workflow.custom_start_stop_events.events.MyCustomStopEvent import MyCustomStopEvent

scenarios("./features/custom_start_stop_agent.feature")


@given("a CustomStartStopEventAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=CustomStartStopEventAgent,
        default_agent_config=CustomStartStopEventAgentConfig(
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
    assert (
        agent_runner.get_event_of_class(MyCustomStopEvent).payload.payload == payload
    ), "Agent received incorrect data"
