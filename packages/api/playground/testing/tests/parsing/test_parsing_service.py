import asyncio
import json
from io import BytesIO
from pathlib import PurePath
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from pypdf import PdfWriter
from swiss_ai_hub.core.generative_ai import MineruLoader, ParseCacheBucket
from swiss_ai_hub.core.infrastructure import MineruSettings

from swiss_ai_hub.api.routes.parsing import parsing_service
from swiss_ai_hub.api.routes.parsing.dto.image_mode import ImageMode
from swiss_ai_hub.api.routes.parsing.parsing_service import MAX_CONCURRENT_MINERU_REQUESTS, ParsingService

UPLOADS_IN_ONE_MESSAGE = 10


@pytest.fixture(autouse=True)
def in_memory_parse_cache(monkeypatch: pytest.MonkeyPatch) -> dict[str, bytes]:
    store: dict[str, bytes] = {}
    monkeypatch.setattr(ParseCacheBucket, "read", lambda _self, key: store.get(key))
    monkeypatch.setattr(
        ParseCacheBucket, "write", lambda _self, key, content, _content_type: store.update({key: content})
    )
    return store


@pytest.fixture
def batch_settings(monkeypatch: pytest.MonkeyPatch):
    def apply(page_batch_size: int, concurrent_batch_requests: int) -> None:
        monkeypatch.setenv("MINERU_PAGE_BATCH_SIZE", str(page_batch_size))
        monkeypatch.setenv("MINERU_MAX_CONCURRENT_BATCH_REQUESTS", str(concurrent_batch_requests))
        monkeypatch.setattr(parsing_service, "_mineru_settings", MineruSettings())

    return apply


def make_pdf(pages: int, marker: int) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    writer.add_metadata({"/Subject": f"upload {marker}"})
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


class MineruRequestTracker:
    """Stands in for MinerU, remembering how many requests it was sent at once."""

    def __init__(self) -> None:
        self.in_flight = 0
        self.most_at_once = 0
        self.requests = 0

    async def execute(
        self,
        file_bytes: bytes,
        filename: str,
        include_images: bool,
        start_page_id: int | None = None,
        end_page_id: int | None = None,
    ) -> SimpleNamespace:
        """Shaped like MinerU's parse response, which is internal to the loader."""
        self.in_flight += 1
        self.requests += 1
        self.most_at_once = max(self.most_at_once, self.in_flight)
        await asyncio.sleep(0.01)
        self.in_flight -= 1
        pages = 1 if start_page_id is None or end_page_id is None else end_page_id - start_page_id + 1
        return SimpleNamespace(
            backend="b",
            version="v",
            results={
                PurePath(filename).stem: {"md_content": filename, "middle_json": json.dumps({"pdf_info": [{}] * pages})}
            },
        )


async def upload(content: bytes, filename: str) -> str:
    response = await ParsingService.convert_from_bytes(
        content=content, filename=filename, content_type="application/pdf", image_mode=ImageMode.BASE64
    )
    return response.page_content


async def upload_all(tracker: MineruRequestTracker, pages: int) -> list[str]:
    with patch.object(MineruLoader, "_execute_conversion", AsyncMock(side_effect=tracker.execute)):
        return await asyncio.gather(
            *(upload(make_pdf(pages, index), f"file_{index}.pdf") for index in range(UPLOADS_IN_ONE_MESSAGE))
        )


@pytest.mark.parametrize("concurrent_batch_requests", [1, 2])
@pytest.mark.asyncio
async def test_should_use_every_request_slot_when_a_message_attaches_ten_short_pdfs(
    batch_settings, concurrent_batch_requests: int
):
    batch_settings(page_batch_size=20, concurrent_batch_requests=concurrent_batch_requests)
    tracker = MineruRequestTracker()

    contents = await upload_all(tracker, pages=3)

    assert tracker.most_at_once == MAX_CONCURRENT_MINERU_REQUESTS
    assert all(content.startswith(f"file_{index}.pdf") for index, content in enumerate(contents))


@pytest.mark.asyncio
async def test_should_send_mineru_no_more_requests_than_the_bound_when_pdfs_are_configured_to_batch_side_by_side(
    batch_settings,
):
    batch_settings(page_batch_size=2, concurrent_batch_requests=4)
    tracker = MineruRequestTracker()

    await upload_all(tracker, pages=8)

    assert tracker.requests == UPLOADS_IN_ONE_MESSAGE * 4
    assert tracker.most_at_once == MAX_CONCURRENT_MINERU_REQUESTS


@pytest.mark.asyncio
async def test_should_serve_a_parsed_upload_from_the_cache_when_every_slot_is_busy(batch_settings):
    batch_settings(page_batch_size=20, concurrent_batch_requests=1)
    tracker = MineruRequestTracker()
    with patch.object(MineruLoader, "_execute_conversion", AsyncMock(side_effect=tracker.execute)):
        await upload(b"pdf", "known.pdf")

        slots = ParsingService.mineru_conversion_slots()
        for _ in range(MAX_CONCURRENT_MINERU_REQUESTS):
            await slots.acquire()
        try:
            content = await asyncio.wait_for(upload(b"pdf", "known.pdf"), timeout=1)
        finally:
            for _ in range(MAX_CONCURRENT_MINERU_REQUESTS):
                slots.release()

    assert content == "known.pdf"
    assert tracker.requests == 1
