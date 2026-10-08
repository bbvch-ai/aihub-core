import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from openpyxl import Workbook

from swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_loader import MarkItDownLoader
from swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_parse_cache import MarkItDownParseCache
from swiss_ai_hub.core.generative_ai.document.loaders.parse_cache_bucket import ParseCacheBucket

DOCX_BYTES = b"docx-bytes"
IMAGE = "data:image/png;base64,iVBORw0KGgo="


@pytest.fixture(autouse=True)
def in_memory_parse_cache(monkeypatch: pytest.MonkeyPatch) -> dict[str, bytes]:
    store: dict[str, bytes] = {}
    monkeypatch.setattr(ParseCacheBucket, "read", lambda self, key: store.get(key))
    monkeypatch.setattr(
        ParseCacheBucket, "write", lambda self, key, content, content_type: store.__setitem__(key, content)
    )
    return store


@pytest.fixture
def markitdown() -> MagicMock:
    return MagicMock(convert=MagicMock(return_value=SimpleNamespace(text_content=f"# Order\n\n![chart]({IMAGE})")))


@pytest.fixture
def loader(markitdown: MagicMock, monkeypatch: pytest.MonkeyPatch) -> MarkItDownLoader:
    loader = MarkItDownLoader()
    monkeypatch.setattr(loader, "_get_converter", lambda: markitdown)
    return loader


def xlsx_bytes() -> bytes:
    book = Workbook()
    book.active.append(["id", "amount"])
    book.active.append([1, 42.31])
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_an_xlsx_is_streamed_without_markitdown(loader: MarkItDownLoader, markitdown: MagicMock):
    documents = await loader.aload_data_from_bytes(xlsx_bytes(), "orders.xlsx", include_images=False)

    assert "| 1 | 42.31 |" in documents[0].text
    markitdown.convert.assert_not_called()


@pytest.mark.asyncio
async def test_other_office_documents_still_go_through_markitdown(loader: MarkItDownLoader, markitdown: MagicMock):
    documents = await loader.aload_data_from_bytes(DOCX_BYTES, "order.docx", include_images=False)

    assert documents[0].text.startswith("# Order")
    markitdown.convert.assert_called_once()


@pytest.mark.asyncio
async def test_a_document_is_converted_once(
    loader: MarkItDownLoader, markitdown: MagicMock, in_memory_parse_cache: dict[str, bytes]
):
    first = await loader.aload_data_from_bytes(DOCX_BYTES, "order.docx", include_images=False)
    second = await MarkItDownLoader().aload_data_from_bytes(DOCX_BYTES, "copy.docx", include_images=False)

    assert second[0].text == first[0].text
    markitdown.convert.assert_called_once()
    assert list(in_memory_parse_cache) == [loader.parse_cache.object_key(DOCX_BYTES, "order.docx")]


@pytest.mark.asyncio
async def test_one_entry_serves_callers_with_and_without_images(loader: MarkItDownLoader, markitdown: MagicMock):
    without_images = await loader.aload_data_from_bytes(DOCX_BYTES, "order.docx", include_images=False)
    with_images = await loader.aload_data_from_bytes(DOCX_BYTES, "order.docx", embed_base64=True)

    assert IMAGE in without_images[0].text
    assert "image/png" in with_images[0].text
    markitdown.convert.assert_called_once()


@pytest.mark.asyncio
async def test_ingestion_reads_what_an_upload_converted(
    loader: MarkItDownLoader, markitdown: MagicMock, tmp_path: Path
):
    stored = tmp_path / "order.docx"
    stored.write_bytes(DOCX_BYTES)

    await loader.aload_data_from_bytes(DOCX_BYTES, "upload.docx", include_images=False)
    documents = await loader.aload_data(str(stored), include_images=False)

    assert documents[0].text.startswith("# Order")
    markitdown.convert.assert_called_once()


@pytest.mark.asyncio
async def test_a_failed_conversion_is_not_cached(
    loader: MarkItDownLoader, markitdown: MagicMock, in_memory_parse_cache: dict[str, bytes]
):
    markitdown.convert.side_effect = ValueError("corrupt document")

    with pytest.raises(ValueError, match="corrupt document"):
        await loader.aload_data_from_bytes(DOCX_BYTES, "order.docx", include_images=False)

    assert in_memory_parse_cache == {}


def test_the_key_depends_on_the_bytes_and_the_extension():
    cache = MarkItDownParseCache()

    key = cache.object_key(DOCX_BYTES, "a.docx")

    assert key.startswith(f"markitdown/{cache.settings_fingerprint()}/")
    assert key.endswith(".docx/markdown.md")
    assert key == cache.object_key(DOCX_BYTES, "another name.DOCX")
    assert key != cache.object_key(DOCX_BYTES, "a.pptx")
    assert key != cache.object_key(b"other bytes", "a.docx")


def test_a_change_to_the_xlsx_rendering_starts_fresh(monkeypatch: pytest.MonkeyPatch):
    fingerprint = MarkItDownParseCache.settings_fingerprint()

    monkeypatch.setattr(MarkItDownParseCache, "XLSX_FORMAT", MarkItDownParseCache.XLSX_FORMAT + 1)

    assert MarkItDownParseCache.settings_fingerprint() != fingerprint


def test_a_new_markitdown_release_starts_fresh(monkeypatch: pytest.MonkeyPatch):
    fingerprint = MarkItDownParseCache.settings_fingerprint()

    monkeypatch.setattr(
        "swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_parse_cache.importlib.metadata.version",
        lambda name: "99.0.0",
    )

    assert MarkItDownParseCache.settings_fingerprint() != fingerprint
