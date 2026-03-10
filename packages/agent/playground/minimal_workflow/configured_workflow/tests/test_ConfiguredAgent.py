from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.control.start.StartEvent import StartEvent
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

from playground.minimal_workflow.configured_workflow.ConfiguredAgent import ConfiguredAgent
from playground.minimal_workflow.configured_workflow.ConfiguredAgentConfig import ConfiguredAgentConfig, StartStepConfig
from playground.minimal_workflow.configured_workflow.events.EventConfiguredA import EventConfiguredA
from playground.minimal_workflow.configured_workflow.events.EventConfiguredB import EventConfiguredB
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner

scenarios("./features/configured_agent.feature")


@given(
    parsers.parse(
        'a ConfiguredAgent runner with a start step value "{start_step_value}" and an agent value "{agent_value}"'
    ),
    target_fixture="agent_runner",
)
def _(start_step_value: str, agent_value: str):
    return AgentTestRunner(
        agent_type=ConfiguredAgent,
        agent_config=ConfiguredAgentConfig(
            agent_id="configured_agent",
            name=LocaleString(en="Configured Agent"),
            description=LocaleString(en="This is a very configured agent"),
            some_agent_value=agent_value,
            start_step_config=StartStepConfig(some_step_value=start_step_value),
        ),
    )


@when("a the start event is sent")
@async_test
async def _(agent_runner: AgentTestRunner):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            start_event=StartEvent(),
            topic=topic,
        )


@then("a StartEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_start_event, "Agent did not receive start event"


@then(parsers.parse('an EventA event is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.get_event_of_class(EventConfiguredA).payload == payload, (
        "Agent received incorrect start step config data"
    )


@then(parsers.parse('an EventB event is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.get_event_of_class(EventConfiguredB).payload == payload, (
        "Agent received incorrect agent config data"
    )


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not receive stop event"
