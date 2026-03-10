from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner
from swiss_ai_hub.core.agents.AgentConfig import AgentConfig
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.processes.ProcessConfig import ProcessConfig
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

from playground.agents.AgentA.AgentA import AgentA
from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.agents.AgentB.AgentB import AgentB
from playground.agents.AgentC.AgentC import AgentC
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.minimal_processes.multi_input_process.MultiInputProcess import MultiInputProcess
from swiss_ai_hub.process.runners.ProcessTestRunner import ProcessTestRunner

scenarios("./features/multi_input_process.feature")


@given("an AgentA runner", target_fixture="agent_a_runner")
def agent_a_runner_fixture():
    return AgentTestRunner(
        agent_type=AgentA,
        agent_config=AgentConfig(
            agent_id="agent_a",
            name=LocaleString(en="Agent A"),
            description=LocaleString(en="Test Agent A"),
        ),
    )


@given("an AgentB runner", target_fixture="agent_b_runner")
def agent_b_runner_fixture():
    return AgentTestRunner(
        agent_type=AgentB,
        agent_config=AgentConfig(
            agent_id="agent_b",
            name=LocaleString(en="Agent B"),
            description=LocaleString(en="Test Agent B"),
        ),
    )


@given("an AgentC runner", target_fixture="agent_c_runner")
def agent_c_runner_fixture():
    return AgentTestRunner(
        agent_type=AgentC,
        agent_config=AgentConfig(
            agent_id="agent_c",
            name=LocaleString(en="Agent C"),
            description=LocaleString(en="Test Agent C"),
        ),
    )


@given("a MultiInputProcess runner", target_fixture="process_runner")
def process_runner_fixture():
    return ProcessTestRunner(
        process_type=MultiInputProcess,
        process_config=ProcessConfig(
            process_id="multi_input_process",
            name=LocaleString(en="Multi Input Process"),
            description=LocaleString(en="Test Multi Input Process"),
        ),
    )


@when(parsers.parse('AgentA is started with payload for MultiInputProcess "{payload}"'))
@async_test
async def agent_a_started_with_payload(
    agent_a_runner: AgentTestRunner,
    agent_b_runner: AgentTestRunner,
    agent_c_runner: AgentTestRunner,
    process_runner: ProcessTestRunner,
    payload: str,
):
    async with process_runner.test_run():
        async with agent_c_runner.test_run():
            async with agent_b_runner.test_run():
                async with agent_a_runner.test_run() as topic_a:
                    await agent_a_runner.send_event_from_topic(
                        start_event=AgentAStartEvent(payload=payload),
                        topic=topic_a,
                    )


@then(parsers.parse('MultiInputProcess produces a CustomProcessStopEvent with payload "{expected_payload}"'))
@async_test
async def verify_process_stop_event(process_runner: ProcessTestRunner, expected_payload: str):
    event = await process_runner.wait_for_event(CustomProcessStopEvent, timeout=10)
    assert isinstance(event, CustomProcessStopEvent), f"Expected CustomProcessStopEvent, got {type(event)}"
    assert event.payload == expected_payload, (
        f"CustomProcessStopEvent payload mismatch. Expected: '{expected_payload}', Got: '{event.payload}'"
    )
