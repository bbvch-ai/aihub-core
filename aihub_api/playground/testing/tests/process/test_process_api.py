import asyncio

import pytest
import pytest_asyncio
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from aihub_api.routes.process.ProcessController import ProcessController
from aihub_api.routes.process.ProcessService import ProcessService
from aihub_api.runners.simulation.process.SimulatedProcessApiTestRunner import SimulatedProcessApiTestRunner

PROCESS_CLASS = "test_process"
PROCESS_ID = "test_process_1"


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def process_api_client():
    auth = DangerousDevelopmentOnlyAuthHandler()
    controller = (
        ProcessController(auth=auth)
        .get_process()
        .get_processes()
        .discover_processes()
        .get_process_start_forms()
        .send_process_start_form()
        .send_process_open_form()
        .get_process_open_forms()
    )
    runner = SimulatedProcessApiTestRunner(
        process_class=PROCESS_CLASS, process_id=PROCESS_ID
    ).with_simple_human_only_process_events()
    runner.mount(controller)
    await runner.start_simulation()
    app = runner.create_app()

    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1") as client:
            yield client


@pytest.fixture(autouse=True)
def cleanup_db_and_cache():
    ProcessService._clear_cache()
    yield
    ProcessService._clear_cache()


@pytest.mark.asyncio(loop_scope="module")
async def test_discover_processes(process_api_client):
    """Test GET /process/discover returns a list containing the simulated process."""
    response = await process_api_client.get("/processes/discover")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert isinstance(data, list), "Response data should be a list"
    found = any(
        process.get("process_class") == PROCESS_CLASS and process.get("process_id") == PROCESS_ID for process in data
    )
    assert found, "Simulated process not found in discovered processes"


@pytest.mark.asyncio(loop_scope="module")
async def test_get_process(process_api_client):
    """Test GET /process/{process_class}/{process_id} returns correct process details."""
    response = await process_api_client.get(f"/processes/{PROCESS_CLASS}/{PROCESS_ID}")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("process_class") == PROCESS_CLASS
    assert data.get("process_id") == PROCESS_ID
    for key in ("process_config", "human_inputs", "program_inputs", "agent_inputs"):
        assert key in data


# TODO: This test currently FAILS due to flawed logic, the test itself is valid. It should be commented back in
# @pytest.mark.asyncio(loop_scope="module")
# async def test_walk_through_process_std_methods(process_api_client):
#     """Play through simple human-only process using standard endpoints"""
#     # Step 1: Get initial form
#     response = await process_api_client.get(f"/processes/{PROCESS_CLASS}/{PROCESS_ID}/start_forms")
#     assert response.status_code == 200, f"Response: {response.text}"
#
#     data = response.json()
#     print(data)
#     assert len(data) == 1
#     assert data[0].get("name") == "HumanStartEvent"
#     assert data[0].get("description") == "HumanStartEvent description"
#     assert data[0].get("route") == "/human_input_0"
#     assert data[0].get("method") == "POST"
#     assert len(data[0].get("form")) == 1
#     assert data[0].get("form")[0].get("formkit") == "primeInputText"
#     assert data[0].get("form")[0].get("name") == "payload"
#     assert not data[0].get("form")[0].get("disabled")
#     assert data[0].get("form")[0].get("label") == "This is some label for HumanStartEvent"
#
#     # Step 2: Send initial form
#     response = await process_api_client.post(
#         f"/processes/{PROCESS_CLASS}/{PROCESS_ID}/submit_start_form",
#         json={"payload": "Initial Payload"},
#         params={"submission_route": "/human_input_0", "submission_method": "POST"},
#     )
#     assert response.status_code == 200, f"Response: {response.text}"
#
#     data = response.json()
#     assert data.get("process_class") == PROCESS_CLASS
#     assert data.get("process_id") == PROCESS_ID
#
#     assert data.get("process_walkthrough_id")
#     process_walkthrough_id = data.get("process_walkthrough_id")
#     await asyncio.sleep(1)
#
#     # Step 3: Check for open forms
#     response = await process_api_client.get(
#         f"/processes/{PROCESS_CLASS}/{PROCESS_ID}/{process_walkthrough_id}/open_forms"
#     )
#     assert response.status_code == 200, f"Response: {response.text}"
#
#     data = response.json()
#     assert len(data) == 1
#     assert data[0].get("name") == "HumanBWork"
#     assert data[0].get("description") == "HumanBWork description"
#     assert data[0].get("route") == "/human_input_1"
#     assert data[0].get("method") == "POST"
#     assert len(data[0].get("form")) == 1
#     assert data[0].get("form")[0].get("formkit") == "primeInputText"
#     assert data[0].get("form")[0].get("name") == "payload"
#     assert not data[0].get("form")[0].get("disabled")
#     assert data[0].get("form")[0].get("label") == "This is some label for HumanBWork"
#     await asyncio.sleep(1)
#
#     # Step 4: Post open form
#     response = await process_api_client.post(
#         f"/processes/{PROCESS_CLASS}/{PROCESS_ID}/{process_walkthrough_id}/submit_open_form",
#         json={"payload": "Second Payload"},
#         params={"submission_route": "/human_input_1", "submission_method": "POST"},
#     )
#     assert response.status_code == 200, f"Response: {response.text}"
#
#     data = response.json()
#     assert data.get("process_class") == PROCESS_CLASS
#     assert data.get("process_id") == PROCESS_ID
#
#     assert data.get("process_walkthrough_id") == process_walkthrough_id
#     await asyncio.sleep(1)
#
#     # Step 5: Assert there a no open forms left
#     response = await process_api_client.get(
#         f"/processes/{PROCESS_CLASS}/{PROCESS_ID}/{process_walkthrough_id}/open_forms"
#     )
#     assert response.status_code == 200, f"Response: {response.text}"
#
#     data = response.json()
#     assert len(data) == 0


@pytest.mark.asyncio(loop_scope="module")
async def test_walk_through_process_dynamic_methods(process_api_client):
    """Play through simple human-only process using dynamically mounted endponts"""
    # Step 1: Get initial form
    response = await process_api_client.get(f"/processes/{PROCESS_CLASS}/{PROCESS_ID}/human_input_0")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("name") == "HumanStartEvent"
    assert data.get("description") == "HumanStartEvent description"
    assert data.get("route") == "/human_input_0"
    assert data.get("method") == "POST"
    assert len(data.get("form")) == 1
    assert data.get("form")[0].get("formkit") == "primeInputText"
    assert data.get("form")[0].get("name") == "payload"
    assert not data.get("form")[0].get("disabled")
    assert data.get("form")[0].get("label") == "This is some label for HumanStartEvent *"

    # Step 2: Send initial form
    response = await process_api_client.post(
        f"/processes/{PROCESS_CLASS}/{PROCESS_ID}/human_input_0",
        json={"payload": "Initial Payload"},
    )
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("process_class") == PROCESS_CLASS
    assert data.get("process_id") == PROCESS_ID

    assert data.get("process_walkthrough_id")
    process_walkthrough_id = data.get("process_walkthrough_id")
    await asyncio.sleep(1)

    # Step 3: Check for open forms
    response = await process_api_client.get(
        f"/processes/{PROCESS_CLASS}/{PROCESS_ID}/{process_walkthrough_id}/human_input_1"
    )
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("name") == "HumanBWork"
    assert data.get("description") == "HumanBWork description"
    assert data.get("route") == "/human_input_1"
    assert data.get("method") == "POST"
    assert len(data.get("form")) == 1
    assert data.get("form")[0].get("formkit") == "primeInputText"
    assert data.get("form")[0].get("name") == "payload"
    assert not data.get("form")[0].get("disabled")
    assert data.get("form")[0].get("label") == "This is some label for HumanBWork"
    await asyncio.sleep(1)

    # Step 4: Post open form
    response = await process_api_client.post(
        f"/processes/{PROCESS_CLASS}/{PROCESS_ID}/{process_walkthrough_id}/human_input_1",
        json={"payload": "Second Payload"},
    )
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("process_class") == PROCESS_CLASS
    assert data.get("process_id") == PROCESS_ID

    assert data.get("process_walkthrough_id") == process_walkthrough_id
