from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.processes import ProcessConfig
from swiss_ai_hub.core.testing import async_test

from playground.agents.AgentA.AgentA import AgentA
from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.minimal_processes.process_sequence.InitialProcess import InitialProcess
from playground.minimal_processes.process_sequence.SubsequentProcess import SubsequentProcess
from swiss_ai_hub.process.runners.process_test_runner import ProcessTestRunner

scenarios("./features/process_sequence.feature")


@given("an AgentA runner for sequence", target_fixture="agent_a_runner")
def agent_a_runner_fixture():
    return AgentTestRunner(
        agent_type=AgentA,
        agent_config=AgentConfig(
            agent_id="agent_a",
            name=LocaleString(en="Agent A for Sequence"),
            description=LocaleString(en="Test Agent A"),
        ),
    )


@given("an InitialProcess runner", target_fixture="initial_process_runner")
def initial_process_runner_fixture():
    return ProcessTestRunner(
        process_type=InitialProcess,
        process_config=ProcessConfig(
            process_id="initial_process",
            name=LocaleString(en="Initial Process"),
            description=LocaleString(en="Test Initial Process"),
        ),
    )


@given("a SubsequentProcess runner", target_fixture="subsequent_process_runner")
def subsequent_process_runner_fixture():
    return ProcessTestRunner(
        process_type=SubsequentProcess,
        process_config=ProcessConfig(
            process_id="subsequent_process",
            name=LocaleString(en="Subsequent Process"),
            description=LocaleString(en="Test Subsequent Process"),
        ),
    )


@when(parsers.parse('AgentA is started with payload for process sequence "{payload}"'))
@async_test
async def agent_a_started_for_sequence(
    agent_a_runner: AgentTestRunner,
    initial_process_runner: ProcessTestRunner,
    subsequent_process_runner: ProcessTestRunner,
    payload: str,
):
    async with subsequent_process_runner.test_run():
        async with initial_process_runner.test_run():
            async with agent_a_runner.test_run() as topic_a:
                await agent_a_runner.send_event_from_topic(
                    start_event=AgentAStartEvent(payload=payload),
                    topic=topic_a,
                )


@then(parsers.parse('SubsequentProcess produces a CustomProcessStopEvent with payload "{expected_payload}"'))
@async_test
async def verify_subsequent_process_stop_event(subsequent_process_runner: ProcessTestRunner, expected_payload: str):
    event = await subsequent_process_runner.wait_for_event(CustomProcessStopEvent, timeout=10)
    assert isinstance(event, CustomProcessStopEvent), f"Expected CustomProcessStopEvent, got {type(event)}"
    assert event.payload == expected_payload, (
        f"CustomProcessStopEvent payload mismatch. Expected: '{expected_payload}', Got: '{event.payload}'"
    )
