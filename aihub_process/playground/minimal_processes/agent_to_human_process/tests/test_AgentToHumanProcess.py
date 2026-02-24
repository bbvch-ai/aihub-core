from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.processes.ProcessConfig import ProcessConfig
from aihub_lib.testing.asyncio_utils.bdd import async_test
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_process.runners.ProcessTestRunner import ProcessTestRunner
from playground.agents.AgentA.AgentA import AgentA
from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.events.HumanBWork import HumanBWork
from playground.events.HumanBWorkReqeust import HumanBWorkRequest
from playground.minimal_processes.agent_to_human_process.AgentToHumanProcess import AgentToHumanProcess

scenarios("./features/agent_to_human_process.feature")


@given("an AgentToHumanProcess runner", target_fixture="process_runner")
def process_runner_fixture():
    return ProcessTestRunner(
        process_type=AgentToHumanProcess,
        process_config=ProcessConfig(
            process_id="agent_to_human_process",
            name=LocaleString(en="Agent To Human Process"),
            description=LocaleString(en="Test Process with Agent and Human"),
        ),
    )


@given("an AgentA runner", target_fixture="agent_a_runner")
def agent_a_runner_fixture():
    return AgentTestRunner(
        agent_type=AgentA,
        agent_config=AgentConfig(
            agent_id="agent_a",
            name=LocaleString(en="Agent A"),
            description=LocaleString(en="Test Agent A for AgentToHumanProcess"),
        ),
    )


@when(
    parsers.parse(
        'AgentA starts the process with payload "{agent_payload}" and a human responds with "{human_payload}"'
    )
)
@async_test
async def agent_starts_and_human_responds(
    process_runner: ProcessTestRunner,
    agent_a_runner: AgentTestRunner,
    agent_payload: str,
    human_payload: str,
):
    async with process_runner.test_run():
        async with agent_a_runner.test_run() as topic_a:
            await agent_a_runner.send_event_from_topic(
                start_event=AgentAStartEvent(payload=agent_payload),
                topic=topic_a,
            )

            # Wait for the process to request human input
            human_work_request = await process_runner.wait_for_event(HumanBWorkRequest, timeout=5.0)
            observed_human_work_request = process_runner.get_topic_and_event_of_class(HumanBWorkRequest)

            # Simulate the human response
            response_payload = f"{human_work_request.forms[0].payload.label.en} -> {human_payload}"
            await process_runner.send_event(
                work_event=HumanBWork(payload=response_payload),
                process_walkthrough_id=observed_human_work_request.topic.process_walkthrough_id,
            )


@then(parsers.parse('AgentToHumanProcess produces a CustomProcessStopEvent with payload "{expected_payload}"'))
@async_test
async def verify_process_stop_event(process_runner: ProcessTestRunner, expected_payload: str):
    event = await process_runner.wait_for_event(CustomProcessStopEvent, timeout=10)
    assert isinstance(event, CustomProcessStopEvent), f"Expected CustomProcessStopEvent, got {type(event)}"
    assert event.payload == expected_payload, (
        f"CustomProcessStopEvent payload mismatch. Expected: '{expected_payload}', Got: '{event.payload}'"
    )
