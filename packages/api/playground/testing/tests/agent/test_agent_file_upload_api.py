from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.testing.auth_utils import TEST_USER_OID, TestAuthHandler

from swiss_ai_hub.api.routes.agent.agent_controller import AgentController
from swiss_ai_hub.api.routes.agent.agent_file_upload_service import AgentFileUploadService
from swiss_ai_hub.api.routes.user_knowledge.user_knowledge_service import UserKnowledgeService
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

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
    auth = TestAuthHandler()
    controller = AgentController(auth=auth).initiate_file_upload().validate_file_upload()
    runner = ApiTestRunner()
    runner.mount(controller)

    from swiss_ai_hub.api.routes.agent.dependencies.use_agent_file_upload import use_agent_file_upload_service

    runner._api_app.dependency_overrides[use_agent_file_upload_service] = lambda: mock_upload_service

    app = runner.create_app()

    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1/active") as c:
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
async def test_initiate_upload_rejects_path_traversal_forward_slash(client):
    response = await client.post(
        f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/files/upload/initiate",
        json={"filename": "../../etc/passwd", "content_type": "application/octet-stream"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_initiate_upload_rejects_path_traversal_backslash(client):
    response = await client.post(
        f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/files/upload/initiate",
        json={"filename": "..\\..\\secret.pdf", "content_type": "application/pdf"},
    )
    assert response.status_code == 422


VALIDATE = f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/files/upload/validate"
THREAD = "65f1c0ffee00000000000001"
MISSING_FILE_ID = "00000000-0000-4000-a000-000000000000"


def _file(file_id: str = VALID_FILE_ID, filename: str = "report.pdf") -> dict[str, str]:
    return {"file_id": file_id, "filename": filename}


@pytest.mark.asyncio
async def test_validate_returns_only_the_missing_files(client, mock_upload_service):
    mock_upload_service.verify_file_exists.side_effect = lambda **kwargs: kwargs["file_id"] != MISSING_FILE_ID

    response = await client.post(VALIDATE, json={"files": [_file(), _file(MISSING_FILE_ID, "gone.pdf")]})

    assert response.status_code == 200, response.text
    assert response.json() == {"missing": [MISSING_FILE_ID]}
    mock_upload_service.verify_file_exists.assert_any_call(
        agent_class=AGENT_CLASS, agent_id=AGENT_ID, file_id=MISSING_FILE_ID, filename="gone.pdf"
    )


@pytest.mark.asyncio
async def test_a_turn_with_a_missing_file_places_nothing(client, mock_upload_service):
    mock_upload_service.verify_file_exists.side_effect = lambda **kwargs: kwargs["file_id"] != MISSING_FILE_ID
    with patch.object(UserKnowledgeService, "place_attachments", new=AsyncMock()) as place:
        response = await client.post(
            VALIDATE, json={"thread_id": THREAD, "files": [_file(), _file(MISSING_FILE_ID, "gone.pdf")]}
        )

    assert response.json() == {"missing": [MISSING_FILE_ID]}
    place.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_complete_turn_places_all_its_files_at_once(client, mock_upload_service):
    mock_upload_service.read_file.side_effect = lambda _class, _id, file_id, filename: f"{file_id}/{filename}".encode()
    with patch.object(UserKnowledgeService, "place_attachments", new=AsyncMock()) as place:
        response = await client.post(
            VALIDATE, json={"thread_id": THREAD, "files": [_file(), _file(MISSING_FILE_ID, "notes.txt")]}
        )

    assert response.status_code == 200, response.text
    assert response.json() == {"missing": []}
    place.assert_awaited_once()
    user, thread_id, files, read = place.await_args.args
    assert (user.id, thread_id) == (TEST_USER_OID, THREAD)
    assert files == {VALID_FILE_ID: "report.pdf", MISSING_FILE_ID: "notes.txt"}
    assert read(VALID_FILE_ID, "report.pdf") == f"{VALID_FILE_ID}/report.pdf".encode()
    mock_upload_service.read_file.assert_called_once_with(AGENT_CLASS, AGENT_ID, VALID_FILE_ID, "report.pdf")


@pytest.mark.asyncio
async def test_a_turn_without_a_conversation_places_nothing(client):
    with patch.object(UserKnowledgeService, "place_attachments", new=AsyncMock()) as place:
        response = await client.post(VALIDATE, json={"files": [_file()]})

    assert response.json() == {"missing": []}
    place.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "file",
    [
        _file("not-a-valid-uuid-string-at-all"),
        _file(""),
        _file(filename="../other-id/secret.pdf"),
        _file(filename="..\\..\\secret.pdf"),
        _file(filename=""),
    ],
)
async def test_a_file_that_is_not_an_upload_is_refused(client, file):
    response = await client.post(VALIDATE, json={"files": [file]})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_a_thread_id_that_is_not_one_is_refused(client):
    response = await client.post(VALIDATE, json={"thread_id": "../../etc", "files": [_file()]})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_a_turn_holds_one_to_a_thousand_files(client, mock_upload_service):
    many = [_file() for _ in range(1000)]

    assert (await client.post(VALIDATE, json={"files": many})).status_code == 200
    assert mock_upload_service.verify_file_exists.call_count == 1000
    assert (await client.post(VALIDATE, json={"files": [*many, _file()]})).status_code == 422
    assert (await client.post(VALIDATE, json={"files": []})).status_code == 422
