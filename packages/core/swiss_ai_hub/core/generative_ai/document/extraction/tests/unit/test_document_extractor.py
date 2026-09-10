import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.schema import Document

from swiss_ai_hub.core.generative_ai.document.extraction.document_extractor import DocumentExtractor
from swiss_ai_hub.core.generative_ai.document.extraction.unsupported_document_type_error import (
    UnsupportedDocumentTypeError,
)
from swiss_ai_hub.core.generative_ai.document.loaders.eml_loader import EmlLoader
from swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_loader import MarkItDownLoader
from swiss_ai_hub.core.generative_ai.document.loaders.mineru_loader import MineruLoader
from swiss_ai_hub.core.generative_ai.document.loaders.raw_loader import RawLoader

_SERVICE = "swiss_ai_hub.core.generative_ai.document.extraction.document_extractor.create_s3_service"
_SELECTOR = "swiss_ai_hub.core.generative_ai.document.loaders.document_loader_selector.DocumentLoaderSelector.for_file"


def _loader_yielding(text: str, metadata: dict | None = None) -> MagicMock:
    loader = MagicMock(spec=MineruLoader)
    loader.aload_data_from_bytes = AsyncMock(return_value=[Document(text=text, extra_info=metadata or {})])
    return loader


def _extract(filename: str, text: str = "# Titel\n\nInhalt.", metadata: dict | None = None, **kwargs):
    with patch(_SELECTOR, return_value=_loader_yielding(text, metadata)):
        return asyncio.run(DocumentExtractor.extract_from_bytes(content=b"x", filename=filename, **kwargs))


class TestRouting:
    """The selector owns the extension map — that is asserted in its own test. What matters here is that the
    extractor asks it, uses what it gets, and records which loader ran."""

    @pytest.mark.parametrize("loader_class", [MineruLoader, EmlLoader, MarkItDownLoader, RawLoader])
    def test_the_loader_the_selector_returns_is_the_one_recorded(self, loader_class):
        # A real instance with only its IO patched: `document_parser` is `type(loader).__name__`, which a
        # `MagicMock(spec=...)` reports as "MagicMock" and would pass this test for the wrong reason.
        loader = loader_class()
        loader.aload_data_from_bytes = AsyncMock(return_value=[Document(text="Inhalt.", extra_info={})])
        with patch(_SELECTOR, return_value=loader) as selector:
            extracted = asyncio.run(
                DocumentExtractor.extract_from_bytes(content=b"x", filename="f.bin", content_type="application/pdf")
            )
        selector.assert_called_once_with("f.bin", "application/pdf")
        assert extracted.document_parser == loader_class.__name__

    def test_no_caller_hint_is_required(self):
        """`content_type` defaults to empty, so a caller that knows only the filename still routes."""
        with patch(_SELECTOR, return_value=_loader_yielding("Inhalt.")) as selector:
            asyncio.run(DocumentExtractor.extract_from_bytes(content=b"x", filename="invoice.pdf"))
        selector.assert_called_once_with("invoice.pdf", "")

    def test_images_are_off_unless_asked_for(self):
        """The loaders demand an fsspec filesystem when images are on, and a classifier prompt has no use for them."""
        loader = _loader_yielding("Inhalt.")
        with patch(_SELECTOR, return_value=loader):
            asyncio.run(DocumentExtractor.extract_from_bytes(content=b"x", filename="a.pdf"))
        assert loader.aload_data_from_bytes.await_args.kwargs["include_images"] is False
        assert loader.aload_data_from_bytes.await_args.kwargs["fs"] is None

    def test_an_unreadable_type_raises_rather_than_returning_empty(self):
        with pytest.raises(UnsupportedDocumentTypeError) as raised:
            asyncio.run(DocumentExtractor.extract_from_bytes(content=b"x", filename="archive.zip"))
        assert "archive.zip" in str(raised.value)
        assert raised.value.extension == "zip"

    def test_a_nameless_file_without_a_content_type_raises(self):
        with pytest.raises(UnsupportedDocumentTypeError):
            asyncio.run(DocumentExtractor.extract_from_bytes(content=b"x", filename="noname"))

    def test_content_type_routes_when_the_filename_carries_no_extension(self):
        """A mail part can arrive as `attachment` with a MIME type and no usable name."""
        extracted = asyncio.run(
            DocumentExtractor.extract_from_bytes(content=b"hello", filename="attachment", content_type="text/plain")
        )
        assert extracted.document_parser == RawLoader.__name__


class TestResultShape:
    def test_title_comes_from_the_first_heading(self):
        assert _extract("2f8c-v2.pdf").title == "Titel"

    def test_title_falls_back_to_the_filename_stem(self):
        assert _extract("invoice-2026.pdf", text="Kein Titel hier.").title == "invoice-2026"

    def test_page_count_is_carried_through_from_loader_metadata(self):
        assert _extract("a.pdf", metadata={"number_of_pages": 7}).number_of_pages == 7

    def test_page_count_is_none_when_the_loader_reports_none(self):
        assert _extract("a.pdf").number_of_pages is None

    def test_content_type_is_guessed_from_the_filename(self):
        assert _extract("a.pdf").content_type == "application/pdf"

    def test_a_caller_supplied_content_type_wins(self):
        assert _extract("a.pdf", content_type="application/x-custom").content_type == "application/x-custom"

    def test_an_unmappable_extension_guesses_a_binary_content_type(self):
        """`mimetypes` maps far more than expected (`.p7m` and even `.xyz` resolve), so the fallback needs an
        extension it genuinely does not know."""
        assert _extract("export.dat").content_type == "application/octet-stream"

    def test_source_filename_is_recorded(self):
        assert _extract("a.pdf").source_filename == "a.pdf"


class TestS3:
    def test_bytes_are_read_from_the_bucket_and_key(self):
        service = MagicMock()
        service.download_file.return_value = b"Subject: Rechnung 42\r\n\r\nBetrag."
        with patch(_SERVICE, return_value=service):
            extracted = asyncio.run(DocumentExtractor.extract_from_s3("knowledge", "mandate/anfrage.eml"))
        service.download_file.assert_called_once_with("knowledge", "mandate/anfrage.eml")
        assert extracted.title == "Rechnung 42"
        assert extracted.source == "s3://knowledge/mandate/anfrage.eml"
        assert extracted.source_filename == "anfrage.eml"

    def test_a_uri_is_split_into_bucket_and_key(self):
        assert DocumentExtractor.split_s3_uri("s3://bucket/nested/key.pdf") == ("bucket", "nested/key.pdf")

    @pytest.mark.parametrize("uri", ["https://bucket/key.pdf", "bucket/key.pdf", "s3://bucket", "s3://", "s3:///key"])
    def test_a_malformed_uri_is_rejected(self, uri):
        with pytest.raises(ValueError):
            DocumentExtractor.split_s3_uri(uri)
