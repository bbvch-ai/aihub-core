"""The whole table of an extraction is downloaded through a link signed for a thread member: found in the thread's own
events, refused to anyone else, and reported as gone once the bucket's retention deleted the file."""

from collections.abc import AsyncGenerator, Iterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from bson import ObjectId
from httpx import ASGITransport, AsyncClient
from mongoengine import DoesNotExist
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.generative_ai import ExtractedTableFile, ExtractionFileStore
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.testing.auth_utils import TEST_USER_EMAIL, TEST_USER_OID, TestAuthHandler

from swiss_ai_hub.api.routes.thread.dto.thread_dto import ThreadDTO
from swiss_ai_hub.api.routes.thread.thread_controller import ThreadController
from swiss_ai_hub.api.routes.thread.thread_service import ThreadService
from swiss_ai_hub.api.routes.user.dto.minimal_user_dto import MinimalUserDTO
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

THREAD_ID = str(ObjectId())
ENDPOINT = f"/api/v1/active/threads/{THREAD_ID}/extracted-tables/x1/download-url"
URL = "https://s3.example.com/agent-files/record-extraction/x1/invoices.csv?X-Amz-Signature=abc"
FILE = ExtractedTableFile(
    bucket=ExtractionFileStore.TABLES_BUCKET,
    key="record-extraction/x1/invoices.csv",
    filename="invoices.csv",
    size=9000,
    row_count=250,
)


@pytest_asyncio.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient]:
    runner = ApiTestRunner()
    runner.mount(ThreadController(auth=TestAuthHandler()).get_extracted_table_download_url())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test") as http:
            yield http


def _thread(member_id: str = TEST_USER_OID) -> ThreadDTO:
    member = MinimalUserDTO(id=member_id, name="Member", email=TEST_USER_EMAIL)
    return ThreadDTO(id=THREAD_ID, name="Invoices", users=[member], agents=[], created_at="2026-10-25T00:00:00")


def _persisted(extraction_id: str = "x1", file: ExtractedTableFile | None = FILE) -> MagicMock:
    event_data: dict[str, Any] = {"extraction_id": extraction_id, "table": "| a |", "summary": "s"}
    if file is not None:
        event_data["file"] = file.model_dump()
    return MagicMock(event_data=event_data)


@pytest.fixture
def thread() -> Iterator[AsyncMock]:
    with patch.object(ThreadService, "get_thread_by_id", new_callable=AsyncMock, return_value=_thread()) as found:
        yield found


@pytest.fixture
def events() -> Iterator[MagicMock]:
    with patch.object(PersistedAgentEventEntity, "display_events_for_thread", return_value=[_persisted()]) as found:
        yield found


@pytest.fixture
def stored() -> Iterator[AsyncMock]:
    with (
        patch.object(ExtractionFileStore, "exists", new_callable=AsyncMock, return_value=True) as exists,
        patch.object(ExtractionFileStore, "download_url", return_value=URL),
    ):
        yield exists


@pytest.mark.asyncio(loop_scope="module")
async def test_a_member_gets_a_link_to_the_whole_table(
    client: AsyncClient, thread: AsyncMock, events: MagicMock, stored: AsyncMock
) -> None:
    response = await client.get(ENDPOINT)

    assert response.status_code == 200, response.text
    assert response.json() == {"url": URL}
    events.assert_called_once_with(THREAD_ID, event_name="RecordsExtractedEvent")
    stored.assert_awaited_once_with(FILE)


@pytest.mark.asyncio(loop_scope="module")
async def test_the_latest_answer_of_an_extraction_is_the_one_downloaded(
    client: AsyncClient, thread: AsyncMock, events: MagicMock, stored: AsyncMock
) -> None:
    confirmed = FILE.model_copy(update={"key": "record-extraction/x1/all.csv", "row_count": 900})
    events.return_value = [_persisted(), _persisted("x2"), _persisted(file=confirmed)]

    await client.get(ENDPOINT)

    stored.assert_awaited_once_with(confirmed)


@pytest.mark.asyncio(loop_scope="module")
async def test_someone_outside_the_thread_gets_no_link(
    client: AsyncClient, thread: AsyncMock, events: MagicMock, stored: AsyncMock
) -> None:
    thread.return_value = _thread(member_id="someone-else")

    with patch.object(AccessChecker, "has_access_to_process", return_value=False):
        response = await client.get(ENDPOINT)

    assert response.status_code == 403
    events.assert_not_called()


@pytest.mark.asyncio(loop_scope="module")
async def test_an_unknown_thread_is_not_found(client: AsyncClient, thread: AsyncMock, stored: AsyncMock) -> None:
    thread.side_effect = DoesNotExist()

    response = await client.get(ENDPOINT)

    assert response.status_code == 404


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize(
    "persisted",
    [
        [],
        [_persisted("x2")],
        [_persisted(file=None)],
        [_persisted(file=FILE.model_copy(update={"bucket": "knowledge"}))],
        [_persisted(file=FILE.model_copy(update={"key": "uploads/someone/payslip.pdf"}))],
    ],
    ids=[
        "no-extraction",
        "another-extraction",
        "inline-table-without-file",
        "not-the-extraction-bucket",
        "another-file-in-the-bucket",
    ],
)
async def test_a_thread_without_that_stored_table_has_none_to_download(
    client: AsyncClient, thread: AsyncMock, events: MagicMock, stored: AsyncMock, persisted: list[MagicMock]
) -> None:
    events.return_value = persisted

    response = await client.get(ENDPOINT)

    assert response.status_code == 404
    stored.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="module")
async def test_a_table_the_retention_deleted_is_reported_gone(
    client: AsyncClient, thread: AsyncMock, events: MagicMock, stored: AsyncMock
) -> None:
    stored.return_value = False

    response = await client.get(ENDPOINT)

    assert response.status_code == 410
    assert "deleted after 7 days" in response.json()["detail"]
