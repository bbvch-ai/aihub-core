import asyncio
import json
import logging
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError
from pypdf import PdfWriter
from tenacity import wait_none

from swiss_ai_hub.core.generative_ai.document.loaders.mineru_loader import (
    MineruFileResult,
    MineruLoader,
    MineruParseResponse,
    MineruRequestError,
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


class TestBatchFailurePropagation:
    @pytest.mark.asyncio
    async def test_batch_failure_replaces_exception_group(self, loader: MineruLoader):
        root_cause = httpx.ConnectError("connection refused")

        async def failing_execute(
            file_bytes: bytes,
            filename: str,
            include_images: bool,
            start_page_id: int | None = None,
            end_page_id: int | None = None,
        ) -> MineruParseResponse:
            if start_page_id == 2:
                raise MineruRequestError("MinerU API rejected the request with status 400") from root_cause
            return make_response(f"pages{start_page_id}", end_page_id - start_page_id + 1)

        pdf_bytes = make_pdf(5)

        with patch.object(loader, "_execute_conversion", AsyncMock(side_effect=failing_execute)):
            with pytest.raises(MineruRequestError, match="status 400") as error:
                await loader.aload_data_from_bytes(pdf_bytes, FILENAME, embed_base64=True)

        assert error.value.__cause__ is root_cause

    def test_unwraps_arbitrarily_nested_groups_and_reports_first_leaf(self, caplog: pytest.LogCaptureFixture):
        first = MineruRequestError("first batch")
        second = MineruTransientError("second batch")
        third = MineruTransientError("third batch")
        group = ExceptionGroup(
            "unhandled errors in a TaskGroup",
            [ExceptionGroup("outer", [ExceptionGroup("inner", [first, ExceptionGroup("deepest", [second])])]), third],
        )

        with caplog.at_level(logging.ERROR):
            assert MineruLoader._unwrap_batch_failure(group, FILENAME) is first

        assert f"3 page batches failed for {FILENAME}" in caplog.text
        assert "second batch" in caplog.text
        assert "third batch" in caplog.text

    def test_single_failure_is_not_logged(self, caplog: pytest.LogCaptureFixture):
        only = MineruTransientError("only batch")

        with caplog.at_level(logging.ERROR):
            assert MineruLoader._unwrap_batch_failure(ExceptionGroup("group", [only]), FILENAME) is only

        assert caplog.text == ""


class TestSettingsValidation:
    def test_zero_concurrency_rejected(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MINERU_MAX_CONCURRENT_BATCH_REQUESTS", "0")
        with pytest.raises(ValidationError):
            MineruLoader()

    def test_negative_batch_size_rejected(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MINERU_PAGE_BATCH_SIZE", "-1")
        with pytest.raises(ValidationError):
            MineruLoader()

    def test_zero_batch_size_allowed(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MINERU_PAGE_BATCH_SIZE", "0")
        assert MineruLoader().config.PAGE_BATCH_SIZE == 0


class TestConversionDeadline:
    @pytest.fixture
    def slow_loader(self, monkeypatch: pytest.MonkeyPatch) -> MineruLoader:
        monkeypatch.setenv("MINERU_API_TIMEOUT", "1")
        monkeypatch.setenv("MINERU_PAGE_BATCH_SIZE", "2")
        monkeypatch.setenv("MINERU_MAX_CONCURRENT_BATCH_REQUESTS", "2")
        return MineruLoader()

    @pytest.mark.asyncio
    async def test_multi_batch_conversion_times_out(self, slow_loader: MineruLoader):
        async def hang_forever(*args: object, **kwargs: object) -> MineruParseResponse:
            await asyncio.sleep(30)
            raise AssertionError("unreachable")

        with patch.object(slow_loader, "_execute_conversion", AsyncMock(side_effect=hang_forever)):
            with pytest.raises(TimeoutError, match="timed out after"):
                await slow_loader.aload_data_from_bytes(make_pdf(4), FILENAME, embed_base64=True)

    @pytest.mark.asyncio
    async def test_unbatched_conversion_times_out(self, slow_loader: MineruLoader):
        async def hang_forever(*args: object, **kwargs: object) -> MineruParseResponse:
            await asyncio.sleep(30)
            raise AssertionError("unreachable")

        with patch.object(slow_loader, "_execute_conversion", AsyncMock(side_effect=hang_forever)):
            with pytest.raises(TimeoutError, match="timed out after"):
                await slow_loader.aload_data_from_bytes(b"png-bytes", "scan.png", embed_base64=True)


class TestErrorClassification:
    def make_http_response(self, status_code: int) -> httpx.Response:
        return httpx.Response(status_code=status_code, text="details")

    def test_server_error_is_transient(self):
        with pytest.raises(MineruTransientError):
            MineruLoader._raise_for_status(self.make_http_response(500), FILENAME)

    def test_capacity_rejection_is_transient(self):
        with pytest.raises(MineruTransientError):
            MineruLoader._raise_for_status(self.make_http_response(503), FILENAME)

    def test_rate_limit_is_transient(self):
        with pytest.raises(MineruTransientError):
            MineruLoader._raise_for_status(self.make_http_response(429), FILENAME)

    def test_client_error_is_not_transient(self):
        with pytest.raises(MineruRequestError):
            MineruLoader._raise_for_status(self.make_http_response(400), FILENAME)

    def test_success_passes(self):
        MineruLoader._raise_for_status(self.make_http_response(200), FILENAME)

    @pytest.mark.asyncio
    async def test_request_error_is_not_retried(self, loader: MineruLoader):
        mock = AsyncMock(side_effect=MineruRequestError("unsupported file type"))
        with patch.object(loader, "_execute_conversion", mock):
            with pytest.raises(MineruRequestError):
                await loader.aload_data_from_bytes(make_pdf(2), FILENAME, embed_base64=True)

        assert mock.await_count == 1

    def test_retry_backoff_outlives_batch_slot_occupancy(self, loader: MineruLoader):
        retry_kwargs = loader._retry_kwargs()
        assert retry_kwargs["stop"].max_attempt_number == 4
        assert retry_kwargs["wait"].min == 5
        assert retry_kwargs["wait"].multiplier == 5


class TestSyncWrapper:
    def test_load_data_round_trips(self, loader: MineruLoader, tmp_path):
        pdf_path = tmp_path / FILENAME
        pdf_path.write_bytes(make_pdf(2))

        mock = AsyncMock(return_value=make_response("content", 2))
        with patch.object(loader, "_execute_conversion", mock):
            documents = loader.load_data(str(pdf_path))

        assert documents[0].text == "content"
        assert documents[0].metadata[NUMBER_OF_PAGES] == 2
