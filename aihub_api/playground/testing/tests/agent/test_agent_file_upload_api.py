from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.infrastructure.s3.AgentFileUploadService import AgentFileUploadService
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.runners.ApiTestRunner import ApiTestRunner

AGENT_CLASS = "TestAgent"
AGENT_ID = "test_1"
VALID_FILE_ID = "aaaabbbb-1111-4222-a333-ccccddddeeee"


@pytest.fixture
def mock_upload_service():
    service = MagicMock(spec=AgentFileUploadService)
    service.generate_upload_url.return_value = (
        "https://s3.example.com/presigned-put-url",
        VALID_FILE_ID,
    )
    service.verify_file_exists.return_value = True
    service.UPLOAD_URL_LIFETIME_SECONDS = 3600
    return service


@pytest_asyncio.fixture
async def client(mock_upload_service):
    auth = DangerousDevelopmentOnlyAuthHandler()
    controller = AgentController(auth=auth).initiate_file_upload().validate_file_upload()
    runner = ApiTestRunner()
    runner.mount(controller)

    from aihub_lib.infrastructure.s3.use_s3 import use_agent_file_upload_service

    runner._api_app.dependency_overrides[use_agent_file_upload_service] = lambda: mock_upload_service

    app = runner.create_app()

    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1") as c:
            yield c


@pytest.mark.asyncio
async def test_initiate_upload_returns_presigned_url(client):
    response = await client.post(
        f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/files/upload/initiate",
        json={"filename": "report.pdf", "content_type": "application/pdf"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["upload_url"] == "https://s3.example.com/presigned-put-url"
    assert data["file_id"] == VALID_FILE_ID
    assert data["expires_in"] == 3600


@pytest.mark.asyncio
async def test_initiate_upload_calls_service_with_correct_args(client, mock_upload_service):
    await client.post(
        f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/files/upload/initiate",
        json={"filename": "image.png", "content_type": "image/png"},
    )
    mock_upload_service.generate_upload_url.assert_called_once_with(
        agent_class=AGENT_CLASS,
        agent_id=AGENT_ID,
        content_type="image/png",
        filename="image.png",
    )


@pytest.mark.asyncio
async def test_initiate_upload_rejects_empty_filename(client):
    response = await client.post(
        f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/files/upload/initiate",
        json={"filename": "", "content_type": "application/pdf"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validate_upload_returns_exists_true(client):
    response = await client.post(
        f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/files/upload/validate",
        json={"file_id": VALID_FILE_ID, "filename": "report.pdf"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["exists"] is True
    assert data["file_id"] == VALID_FILE_ID


@pytest.mark.asyncio
async def test_validate_upload_returns_exists_false(client, mock_upload_service):
    mock_upload_service.verify_file_exists.return_value = False
    missing_file_id = "00000000-0000-4000-a000-000000000000"

    response = await client.post(
        f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/files/upload/validate",
        json={"file_id": missing_file_id, "filename": "missing.pdf"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["exists"] is False


@pytest.mark.asyncio
async def test_validate_upload_rejects_non_uuid_file_id(client):
    response = await client.post(
        f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/files/upload/validate",
        json={"file_id": "not-a-valid-uuid-string-at-all", "filename": "test.pdf"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validate_upload_rejects_empty_file_id(client):
    response = await client.post(
        f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/files/upload/validate",
        json={"file_id": "", "filename": "test.pdf"},
    )
    assert response.status_code == 422
