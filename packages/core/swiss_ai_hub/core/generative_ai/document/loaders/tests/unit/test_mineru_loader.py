import asyncio
import json
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pypdf import PdfWriter
from tenacity import wait_none

from swiss_ai_hub.core.generative_ai.document.loaders.mineru_loader import (
    MineruFileResult,
    MineruLoader,
    MineruParseResponse,
    MineruTransientError,
)
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NUMBER_OF_PAGES

FILENAME = "document.pdf"
STEM = "document"


def make_pdf(num_pages: int) -> bytes:
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def make_response(
    md: str,
    num_pages: int,
    images: dict[str, str] | None = None,
    stem: str = STEM,
) -> MineruParseResponse:
    return MineruParseResponse(
        backend="vlm-http-client",
        version="2.7.5",
        results={
            stem: {
                "md_content": md,
                "middle_json": json.dumps({"pdf_info": [{}] * num_pages}),
                "images": images or {},
            }
        },
    )


def fast_retry_kwargs(loader: MineruLoader) -> dict:
    kwargs = MineruLoader._retry_kwargs(loader)
    kwargs["wait"] = wait_none()
    return kwargs


@pytest.fixture
def loader(monkeypatch: pytest.MonkeyPatch) -> MineruLoader:
    monkeypatch.setenv("MINERU_PAGE_BATCH_SIZE", "2")
    monkeypatch.setenv("MINERU_MAX_CONCURRENT_BATCH_REQUESTS", "2")
    return MineruLoader()


class TestPageProbe:
    def test_count_pdf_pages(self):
        assert MineruLoader._count_pdf_pages(make_pdf(5)) == 5

    def test_page_ranges_exact_multiple(self):
        assert MineruLoader._page_ranges(50, 25) == [(0, 24), (25, 49)]

    def test_page_ranges_with_remainder(self):
        assert MineruLoader._page_ranges(51, 25) == [(0, 24), (25, 49), (50, 50)]

    def test_page_ranges_single_batch(self):
        assert MineruLoader._page_ranges(10, 25) == [(0, 9)]

    def test_page_ranges_zero_pages(self):
        assert MineruLoader._page_ranges(0, 25) == []


class TestMergeResults:
    def test_merges_markdown_pages_and_images(self):
        results = [
            MineruFileResult(
                backend="vlm-http-client", version="2.7.5", md_content="first", num_pages=2, images={"a.jpg": "1"}
            ),
            MineruFileResult(
                backend="vlm-http-client", version="2.7.5", md_content="", num_pages=2, images={"b.jpg": "2"}
            ),
            MineruFileResult(
                backend="vlm-http-client", version="2.7.5", md_content="last", num_pages=1, images={"a.jpg": "1"}
            ),
        ]

        merged = MineruLoader._merge_results(results)

        assert merged.md_content == "first\n\nlast"
        assert merged.num_pages == 5
        assert merged.images == {"a.jpg": "1", "b.jpg": "2"}
        assert merged.backend == "vlm-http-client"
        assert merged.version == "2.7.5"


class TestBatching:
    @pytest.mark.asyncio
    async def test_small_pdf_single_unbatched_request(self, loader: MineruLoader):
        mock = AsyncMock(return_value=make_response("content", 2))
        with patch.object(loader, "_execute_conversion", mock):
            documents = await loader.aload_data_from_bytes(make_pdf(2), FILENAME, embed_base64=True)

        assert mock.await_count == 1
        assert mock.await_args.args[3] is None
        assert mock.await_args.args[4] is None
        assert documents[0].text == "content"
        assert documents[0].metadata[NUMBER_OF_PAGES] == 2

    @pytest.mark.asyncio
    async def test_batch_size_zero_disables_batching(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MINERU_PAGE_BATCH_SIZE", "0")
        loader = MineruLoader()
        mock = AsyncMock(return_value=make_response("content", 5))
        probe = MagicMock()
        with patch.object(loader, "_execute_conversion", mock), patch.object(loader, "_count_pdf_pages", probe):
            await loader.aload_data_from_bytes(make_pdf(5), FILENAME, embed_base64=True)

        assert mock.await_count == 1
        probe.assert_not_called()

    @pytest.mark.asyncio
    async def test_multi_batch_stitching_in_page_order(self, loader: MineruLoader):
        async def fake_execute(
            file_bytes: bytes,
            filename: str,
            include_images: bool,
            start_page_id: int | None = None,
            end_page_id: int | None = None,
        ) -> MineruParseResponse:
            return MineruParseResponse(
                backend="vlm-http-client",
                version="2.7.5",
                results={
                    STEM: {
                        "md_content": f"pages{start_page_id}-{end_page_id}",
                        "middle_json": json.dumps({"pdf_info": [{}] * (end_page_id - start_page_id + 1)}),
                        "images": {f"img{start_page_id}.jpg": "data"},
                    }
                },
            )

        mock = AsyncMock(side_effect=fake_execute)
        with patch.object(loader, "_execute_conversion", mock):
            documents = await loader.aload_data_from_bytes(make_pdf(5), FILENAME, embed_base64=True)

        assert mock.await_count == 3
        requested_ranges = sorted((call.args[3], call.args[4]) for call in mock.await_args_list)
        assert requested_ranges == [(0, 1), (2, 3), (4, 4)]
        assert documents[0].text == "pages0-1\n\npages2-3\n\npages4-4"
        assert documents[0].metadata[NUMBER_OF_PAGES] == 5

    @pytest.mark.asyncio
    async def test_non_pdf_bypasses_batching(self, loader: MineruLoader):
        mock = AsyncMock(return_value=make_response("scan", 1, stem="scan"))
        probe = MagicMock()
        with patch.object(loader, "_execute_conversion", mock), patch.object(loader, "_count_pdf_pages", probe):
            await loader.aload_data_from_bytes(b"png-bytes", "scan.png", embed_base64=True)

        assert mock.await_count == 1
        assert mock.await_args.args[3] is None
        probe.assert_not_called()

    @pytest.mark.asyncio
    async def test_failed_batch_retries_independently(self, loader: MineruLoader):
        attempts_per_range: dict[int, int] = {}

        async def flaky_execute(
            file_bytes: bytes,
            filename: str,
            include_images: bool,
            start_page_id: int | None = None,
            end_page_id: int | None = None,
        ) -> MineruParseResponse:
            attempts_per_range[start_page_id] = attempts_per_range.get(start_page_id, 0) + 1
            if start_page_id == 2 and attempts_per_range[start_page_id] == 1:
                raise MineruTransientError("transient failure")
            return make_response(f"pages{start_page_id}", end_page_id - start_page_id + 1)

        with (
            patch.object(loader, "_execute_conversion", AsyncMock(side_effect=flaky_execute)),
            patch.object(loader, "_retry_kwargs", lambda: fast_retry_kwargs(loader)),
        ):
            documents = await loader.aload_data_from_bytes(make_pdf(5), FILENAME, embed_base64=True)

        assert attempts_per_range == {0: 1, 2: 2, 4: 1}
        assert documents[0].metadata[NUMBER_OF_PAGES] == 5

    @pytest.mark.asyncio
    async def test_concurrency_bounded_by_setting(self, loader: MineruLoader):
        in_flight = 0
        max_in_flight = 0

        async def tracking_execute(
            file_bytes: bytes,
            filename: str,
            include_images: bool,
            start_page_id: int | None = None,
            end_page_id: int | None = None,
        ) -> MineruParseResponse:
            nonlocal in_flight, max_in_flight
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
            await asyncio.sleep(0.01)
            in_flight -= 1
            return make_response(f"pages{start_page_id}", end_page_id - start_page_id + 1)

        with patch.object(loader, "_execute_conversion", AsyncMock(side_effect=tracking_execute)):
            await loader.aload_data_from_bytes(make_pdf(12), FILENAME, embed_base64=True)

        assert max_in_flight <= 2

    @pytest.mark.asyncio
    async def test_corrupt_pdf_falls_back_to_unbatched(self, loader: MineruLoader):
        mock = AsyncMock(return_value=make_response("content", 1))
        with patch.object(loader, "_execute_conversion", mock):
            documents = await loader.aload_data_from_bytes(b"not a pdf", FILENAME, embed_base64=True)

        assert mock.await_count == 1
        assert mock.await_args.args[3] is None
        assert documents[0].text == "content"


class TestSyncWrapper:
    def test_load_data_round_trips(self, loader: MineruLoader, tmp_path):
        pdf_path = tmp_path / FILENAME
        pdf_path.write_bytes(make_pdf(2))

        mock = AsyncMock(return_value=make_response("content", 2))
        with patch.object(loader, "_execute_conversion", mock):
            documents = loader.load_data(str(pdf_path))

        assert documents[0].text == "content"
        assert documents[0].metadata[NUMBER_OF_PAGES] == 2
