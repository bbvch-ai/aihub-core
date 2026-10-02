"""The user's own file space over the code sandbox: their home only, as their own account, with sandbox refusals passed
on and every path kept inside the home."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.infrastructure import OpenTerminalError
from swiss_ai_hub.core.testing.auth_utils import TEST_USER_OID, TestAuthHandler

from swiss_ai_hub.api.routes.user_knowledge import user_knowledge_service
from swiss_ai_hub.api.routes.user_knowledge.user_knowledge_controller import UserKnowledgeController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

ENDPOINT = "/api/v1/active/user-knowledge"
THREAD = "65f1c0ffee00000000000001"


@pytest_asyncio.fixture(scope="module")
async def client():
    runner = ApiTestRunner()
    controller = UserKnowledgeController(auth=TestAuthHandler())
    (
        controller.list_user_files()
        .get_user_file_content()
        .upload_user_file()
        .create_user_folder()
        .move_user_file()
        .delete_user_file()
    )
    runner.mount(controller)
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test") as http:
            yield http


@pytest.fixture
def sandbox() -> Any:
    fake = MagicMock()
    fake.list_files = AsyncMock(
        return_value={
            "dir": "/home/owui1234",
            "entries": [
                {"name": "report.pdf", "type": "file", "size": 1200, "modified": 1.0},
                {"name": ".cache", "type": "directory", "size": 4096, "modified": 1.0},
                {"name": "conversations", "type": "directory", "size": 4096, "modified": 2.0},
            ],
        }
    )
    fake.view = AsyncMock(return_value=(b"%PDF-1.7", "application/pdf"))
    fake.upload = AsyncMock(return_value={})
    fake.mkdir = AsyncMock(return_value={})
    fake.move = AsyncMock(return_value={})
    fake.delete = AsyncMock(return_value={})
    with (
        patch.object(
            user_knowledge_service.OpenWebuiAccountEntity, "openwebui_id_of", return_value="owui-1234"
        ) as id_of,
        patch.object(user_knowledge_service, "OpenTerminalClient", return_value=fake) as created,
    ):
        fake.id_of, fake.created = id_of, created
        yield fake


@pytest.mark.asyncio
async def test_the_listing_is_the_user_s_own_home_without_dotfiles(client: AsyncClient, sandbox: Any) -> None:
    response = await client.get(ENDPOINT)

    assert response.status_code == 200
    sandbox.id_of.assert_called_once_with(TEST_USER_OID)
    sandbox.created.assert_called_once_with("owui-1234")
    assert [(entry["name"], entry["kind"]) for entry in response.json()["entries"]] == [
        ("conversations", "folder"),
        ("report.pdf", "file"),
    ]


@pytest.mark.asyncio
async def test_conversation_folders_carry_the_chat_title(client: AsyncClient, sandbox: Any) -> None:
    sandbox.list_files.return_value = {"entries": [{"name": THREAD, "type": "directory", "modified": 1.0}]}
    with patch.object(
        user_knowledge_service.UserKnowledgeService, "_conversation_titles", return_value={THREAD: "Q1 sales"}
    ) as titles:
        response = await client.get(ENDPOINT, params={"folder": "conversations"})

    titles.assert_called_once()
    assert response.json()["entries"][0]["conversation_title"] == "Q1 sales"


@pytest.mark.asyncio
async def test_a_download_returns_the_bytes_as_an_attachment(client: AsyncClient, sandbox: Any) -> None:
    response = await client.get(f"{ENDPOINT}/content", params={"path": "reports/Q1 report.pdf", "download": True})

    assert response.content == b"%PDF-1.7"
    assert response.headers["content-disposition"] == "attachment; filename*=UTF-8''Q1%20report.pdf"
    assert response.headers["x-content-type-options"] == "nosniff"
    sandbox.view.assert_awaited_once_with("reports/Q1 report.pdf")


@pytest.mark.asyncio
async def test_a_pdf_is_shown_in_place(client: AsyncClient, sandbox: Any) -> None:
    response = await client.get(f"{ENDPOINT}/content", params={"path": "report.pdf"})

    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("inline;")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content_type", ["text/html", "image/svg+xml", "application/xhtml+xml", "text/html; charset=utf-8"]
)
async def test_a_file_a_browser_could_run_script_from_is_never_shown_in_place(
    client: AsyncClient, sandbox: Any, content_type: str
) -> None:
    sandbox.view.return_value = (b"<script>alert(1)</script>", content_type)

    response = await client.get(f"{ENDPOINT}/content", params={"path": "page.html"})

    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-disposition"].startswith("attachment;")
    assert response.headers["content-security-policy"] == "sandbox; default-src 'none'"


@pytest.mark.asyncio
async def test_an_upload_lands_in_the_chosen_folder(client: AsyncClient, sandbox: Any) -> None:
    response = await client.post(f"{ENDPOINT}/files", params={"folder": "notes"}, files={"file": ("a.txt", b"hi")})

    assert response.json() == {"path": "notes/a.txt"}
    sandbox.upload.assert_awaited_once_with("notes", "a.txt", b"hi")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "url", "kwargs"),
    [
        ("get", ENDPOINT, {"params": {"folder": "/etc"}}),
        ("get", f"{ENDPOINT}/content", {"params": {"path": "../../proc/1/environ"}}),
        ("post", f"{ENDPOINT}/folders", {"json": {"path": "~/../other"}}),
        ("post", f"{ENDPOINT}/move", {"json": {"source": "a.txt", "destination": "/tmp/a.txt"}}),
        ("delete", ENDPOINT, {"params": {"path": "."}}),
    ],
)
async def test_a_path_outside_the_home_or_the_top_itself_is_refused(
    client: AsyncClient, sandbox: Any, method: str, url: str, kwargs: dict
) -> None:
    response = await getattr(client, method)(url, **kwargs)

    assert response.status_code == 400
    sandbox.view.assert_not_awaited()
    sandbox.move.assert_not_awaited()
    sandbox.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_rename_moves_within_the_folder(client: AsyncClient, sandbox: Any) -> None:
    response = await client.post(f"{ENDPOINT}/move", json={"source": "notes/a.txt", "destination": "notes/b.txt"})

    assert response.json() == {"path": "notes/b.txt"}
    sandbox.move.assert_awaited_once_with("notes/a.txt", "notes/b.txt")


@pytest.mark.asyncio
async def test_a_user_without_a_chat_account_has_no_file_space_yet(client: AsyncClient, sandbox: Any) -> None:
    sandbox.id_of.return_value = None

    response = await client.get(ENDPOINT)

    assert response.status_code == 404
    sandbox.list_files.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_sandbox_refusal_is_passed_on_and_a_failure_is_a_bad_gateway(client: AsyncClient, sandbox: Any) -> None:
    sandbox.delete.side_effect = OpenTerminalError("404: Path not found", 404)
    missing = await client.delete(ENDPOINT, params={"path": "gone.txt"})
    sandbox.list_files.side_effect = OpenTerminalError("500: boom", 500)
    broken = await client.get(ENDPOINT)

    assert (missing.status_code, missing.json()["detail"]) == (404, "404: Path not found")
    assert (broken.status_code, broken.json()["detail"]) == (502, "The code sandbox did not respond.")
