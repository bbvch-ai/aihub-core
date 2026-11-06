import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from swiss_ai_hub.core.generative_ai import MineruLoader, ParseCacheBucket
from swiss_ai_hub.core.generative_ai.document.loaders.mineru_file_result import MineruFileResult

from swiss_ai_hub.api.routes.parsing.dto.image_mode import ImageMode
from swiss_ai_hub.api.routes.parsing.parsing_service import MAX_CONCURRENT_MINERU_CONVERSIONS, ParsingService

UPLOADS_IN_ONE_MESSAGE = 10


@pytest.fixture(autouse=True)
def in_memory_parse_cache(monkeypatch: pytest.MonkeyPatch) -> dict[str, bytes]:
    store: dict[str, bytes] = {}
    monkeypatch.setattr(ParseCacheBucket, "read", lambda _self, key: store.get(key))
    monkeypatch.setattr(
        ParseCacheBucket, "write", lambda _self, key, content, _content_type: store.update({key: content})
    )
    return store


class ConversionTracker:
    """Stands in for MinerU, remembering how many conversions it was asked to run at once."""

    def __init__(self) -> None:
        self.in_flight = 0
        self.most_at_once = 0
        self.conversions = 0

    async def convert(self, file_bytes: bytes, filename: str, include_images: bool) -> MineruFileResult:
        self.in_flight += 1
        self.conversions += 1
        self.most_at_once = max(self.most_at_once, self.in_flight)
        await asyncio.sleep(0.01)
        self.in_flight -= 1
        return MineruFileResult(backend="b", version="v", md_content=filename, num_pages=1, images={})


async def upload(content: bytes, filename: str) -> str:
    response = await ParsingService.convert_from_bytes(
        content=content, filename=filename, content_type="application/pdf", image_mode=ImageMode.BASE64
    )
    return response.page_content


@pytest.mark.asyncio
async def test_should_convert_no_more_uploads_at_once_than_mineru_slots_when_a_message_attaches_ten_pdfs():
    tracker = ConversionTracker()

    with patch.object(MineruLoader, "_convert_uncached", AsyncMock(side_effect=tracker.convert)):
        contents = await asyncio.gather(
            *(upload(f"pdf {index}".encode(), f"file_{index}.pdf") for index in range(UPLOADS_IN_ONE_MESSAGE))
        )

    assert tracker.most_at_once == MAX_CONCURRENT_MINERU_CONVERSIONS
    assert contents == [f"file_{index}.pdf" for index in range(UPLOADS_IN_ONE_MESSAGE)]


@pytest.mark.asyncio
async def test_should_serve_a_parsed_upload_from_the_cache_when_every_slot_is_busy():
    tracker = ConversionTracker()
    with patch.object(MineruLoader, "_convert_uncached", AsyncMock(side_effect=tracker.convert)):
        await upload(b"pdf", "known.pdf")

        slots = ParsingService.mineru_conversion_slots()
        for _ in range(MAX_CONCURRENT_MINERU_CONVERSIONS):
            await slots.acquire()
        try:
            content = await asyncio.wait_for(upload(b"pdf", "known.pdf"), timeout=1)
        finally:
            for _ in range(MAX_CONCURRENT_MINERU_CONVERSIONS):
                slots.release()

    assert content == "known.pdf"
    assert tracker.conversions == 1
