from pytest_bdd import scenarios, given, when, then, parsers
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from playground.minimal_workflow.configured_workflow.events.EventA import EventA
from playground.minimal_workflow.configured_workflow.ConfiguredAgent import (
    ConfiguredAgent,
)
from playground.minimal_workflow.configured_workflow.ConfiguredAgentConfig import (
    ConfiguredAgentConfig,
    StartStepConfig,
)

scenarios("../tests/features/configured_agent.feature")


@given(
    parsers.parse(
        'a ConfiguredAgent runner with agent value "{agent_value}" and step value "{step_value}"'
    ),
    target_fixture="agent_runner",
)
def _(agent_value: str, step_value: str):
    return AgentTestRunner(
        agent_type=ConfiguredAgent,
        agent_config=ConfiguredAgentConfig(
            agent_id="configured_agent",
            name=LocaleString(en="Configured Agent"),
            description=LocaleString(en="This is a configured agent"),
            system_prompt=LocaleString(en="You are an agent"),
            some_agent_value=agent_value,
            start_step_config=StartStepConfig(
                some_step_value=step_value,
            ),
        ),
    )


@when(parsers.parse("the start event is sent"))
@async_test
async def _(agent_runner: AgentTestRunner):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            start_event=StartEvent(),
            topic=topic,
        )


@then("an EventA event is present")
def _(agent_runner: AgentTestRunner):
    event = agent_runner.get_event_of_type(EventA)
    assert event is not None, "EventA was not received"


@then(parsers.parse('the agent configuration value "{agent_value}" is processed'))
def _(agent_runner: AgentTestRunner, agent_value: str):
    processed_value = agent_runner.agent_config.some_agent_value
    assert (
        processed_value == agent_value
    ), f"Agent configuration was not processed correctly. Expected: {agent_value}, Got: {processed_value}"


@then(parsers.parse('the step configuration value "{step_value}" is processed'))
def _(agent_runner: AgentTestRunner, step_value: str):
    processed_value = agent_runner.agent_config.get_step_configs()[
        StartStepConfig
    ].some_step_value
    assert (
        processed_value == step_value
    ), f"Step configuration was not processed correctly. Expected: {step_value}, Got: {processed_value}"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "StopEvent was not received"
