from bson import ObjectId
from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.processes import ProcessConfig
from swiss_ai_hub.core.testing import async_test

from playground.events.custom_process_stop_event import CustomProcessStopEvent
from playground.events.human_a_work import HumanAWork
from playground.events.human_b_work import HumanBWork
from playground.events.human_b_work_reqeust import HumanBWorkRequest
from playground.minimal_processes.human_only_process.human_only_process import HumanOnlyProcess
from swiss_ai_hub.process.runners.process_test_runner import ProcessTestRunner

scenarios("./features/human_only_process.feature")

enable_logging()


@given("a HumanOnlyProcessRunner runner", target_fixture="process_runner")
def process_runner_fixture():
    return ProcessTestRunner(
        process_type=HumanOnlyProcess,
        process_config=ProcessConfig(
            process_id="human_only_process",
            name=LocaleString(en="Human Only Process"),
            description=LocaleString(en="Test Human Only Process with HumanA and HumanB"),
        ),
    )


@when(parsers.parse('HumanA sends work with payload "{payload_a}" and HumanB responds with payload "{payload_b}"'))
@async_test
async def human_b_work_with_payload(process_runner: ProcessTestRunner, payload_a: str, payload_b):
    process_walkthrough_id = str(ObjectId())
    async with process_runner.test_run():
        await process_runner.send_event(
            work_event=HumanAWork(payload=payload_a),
            process_walkthrough_id=process_walkthrough_id,
        )
        human_b_work_request = await process_runner.wait_for_event(HumanBWorkRequest, timeout=5.0)
        payload = f"{human_b_work_request.forms[0].payload.label.en} -> {payload_b}"
        await process_runner.send_event(
            work_event=HumanBWork(payload=payload),
            process_walkthrough_id=process_walkthrough_id,
        )


@then(parsers.parse('HumanOnlyProcessRunner produces a CustomProcessStopEvent with payload "{expected_payload}"'))
@async_test
async def verify_process_stop_event(process_runner: ProcessTestRunner, expected_payload: str):
    event = await process_runner.wait_for_event(CustomProcessStopEvent, timeout=3)
    assert isinstance(event, CustomProcessStopEvent), f"Expected CustomProcessStopEvent, got {type(event)}"
    assert event.payload == expected_payload, (
        f"CustomProcessStopEvent payload mismatch. Expected: '{expected_payload}', Got: '{event.payload}'"
    )
