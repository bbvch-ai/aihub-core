import asyncio
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence.process import ProcessClassEntity
from swiss_ai_hub.core.persistence.process.process_class_entity import HumanInSpecsEntity
from swiss_ai_hub.core.persistence.process.process_config_entity_document import ProcessConfigEntityDocument
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.api.routes.process.process_controller import ProcessController
from swiss_ai_hub.api.runners.simulation.process.simulated_process_api_test_runner import SimulatedProcessApiTestRunner

pytestmark = pytest.mark.usefixtures("setup_process_config_mock")

PROCESS_CLASS = "test_process"
PROCESS_ID = "test_process_1"


@pytest.fixture(scope="module")
def setup_process_config_mock():
    """Set up mock for ProcessConfigEntityDocument.find_for_class_and_id."""
    mock_entity = Mock(spec=ProcessConfigEntityDocument)
    mock_entity.process_class = PROCESS_CLASS
    mock_entity.process_id = PROCESS_ID
    mock_entity.name = LocaleString(en="Test Process")
    mock_entity.description = LocaleString(en="Test Process Description")

    patcher = patch.object(ProcessConfigEntityDocument, "find_for_class_and_id")
    mock_find = patcher.start()

    def find_impl(process_class, process_id):
        if process_class == PROCESS_CLASS and process_id == PROCESS_ID:
            return mock_entity
        return None

    mock_find.side_effect = find_impl
    yield mock_find
    patcher.stop()


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def process_api_client(setup_process_config_mock):
    auth = TestAuthHandler()
    controller = (
        ProcessController(auth=auth)
        .get_process_classes()
        .get_process_class()
        .get_process_class_instances()
        .get_process_instance()
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

    # Mock ProcessClassEntity.get_by_process_class to return an entity
    # with the human_inputs that the simulated runner created.
    human_input_entities = [HumanInSpecsEntity.from_specs(specs) for specs in runner.human_inputs]
    mock_class_entity = Mock(spec=ProcessClassEntity)
    mock_class_entity.process_class = PROCESS_CLASS
    mock_class_entity.human_inputs = human_input_entities
    mock_class_entity.is_online = True

    class_patcher = patch.object(ProcessClassEntity, "get_by_process_class", return_value=mock_class_entity)
    class_patcher.start()

    app = runner.create_app()

    async with LifespanManager(app) as lifespan:
        async with AsyncClient(
            transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1/active"
        ) as client:
            yield client

    class_patcher.stop()


@pytest.mark.asyncio(loop_scope="module")
async def test_walk_through_process_dynamic_methods(process_api_client):
    """Play through simple human-only process using dynamically mounted endpoints.

    The dynamically registered endpoints now use the class-based URL pattern:
    /processes/classes/{process_class}/instances/{process_id}/...
    """
    # Step 1: Get initial form (class-based URL pattern with {process_id} path param)
    response = await process_api_client.get(f"/processes/classes/{PROCESS_CLASS}/instances/{PROCESS_ID}/human_input_0")
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
        f"/processes/classes/{PROCESS_CLASS}/instances/{PROCESS_ID}/human_input_0",
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
        f"/processes/classes/{PROCESS_CLASS}/instances/{PROCESS_ID}/{process_walkthrough_id}/human_input_1"
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
        f"/processes/classes/{PROCESS_CLASS}/instances/{PROCESS_ID}/{process_walkthrough_id}/human_input_1",
        json={"payload": "Second Payload"},
    )
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("process_class") == PROCESS_CLASS
    assert data.get("process_id") == PROCESS_ID

    assert data.get("process_walkthrough_id") == process_walkthrough_id
