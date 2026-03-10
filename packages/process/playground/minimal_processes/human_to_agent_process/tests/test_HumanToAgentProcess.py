from bson import ObjectId
from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner
from swiss_ai_hub.core.agents.AgentConfig import AgentConfig
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.processes.ProcessConfig import ProcessConfig
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

from playground.agents.AgentA.AgentA import AgentA
from playground.events.AgentAWorkRequest import AgentAWorkRequest
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.events.HumanAWork import HumanAWork
from playground.minimal_processes.human_to_agent_process.HumanToAgentProcess import HumanToAgentProcess
from swiss_ai_hub.process.runners.ProcessTestRunner import ProcessTestRunner

scenarios("./features/human_to_agent_process.feature")


@given("a HumanToAgentProcess runner", target_fixture="process_runner")
def process_runner_fixture():
    return ProcessTestRunner(
        process_type=HumanToAgentProcess,
        process_config=ProcessConfig(
            process_id="human_to_agent_process",
            name=LocaleString(en="Human To Agent Process"),
            description=LocaleString(en="Test Process with Human and Agent"),
        ),
    )


@given("an AgentA runner", target_fixture="agent_a_runner")
def agent_a_runner_fixture():
    return AgentTestRunner(
        agent_type=AgentA,
        agent_config=AgentConfig(
            agent_id="agent_a",
            name=LocaleString(en="Agent A"),
            description=LocaleString(en="Test Agent A for HumanToAgentProcess"),
        ),
    )


@when(parsers.parse('a human sends work with payload "{payload}"'))
@async_test
async def human_sends_work(
    process_runner: ProcessTestRunner,
    agent_a_runner: AgentTestRunner,
    payload: str,
):
    process_walkthrough_id = str(ObjectId())
    async with process_runner.test_run():
        async with agent_a_runner.test_run():
            await process_runner.send_event(
                work_event=HumanAWork(payload=payload),
                process_walkthrough_id=process_walkthrough_id,
            )
            # Wait for the process to request work from AgentA
            await process_runner.wait_for_event(AgentAWorkRequest, timeout=5.0)


@then(parsers.parse('HumanToAgentProcess produces a CustomProcessStopEvent with payload "{expected_payload}"'))
@async_test
async def verify_process_stop_event(process_runner: ProcessTestRunner, expected_payload: str):
    event = await process_runner.wait_for_event(CustomProcessStopEvent, timeout=10)
    assert isinstance(event, CustomProcessStopEvent), f"Expected CustomProcessStopEvent, got {type(event)}"
    assert event.payload == expected_payload, (
        f"CustomProcessStopEvent payload mismatch. Expected: '{expected_payload}', Got: '{event.payload}'"
    )
