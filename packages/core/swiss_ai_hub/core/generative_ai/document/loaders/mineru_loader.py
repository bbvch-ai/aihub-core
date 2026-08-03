import asyncio
import json
import logging
import math
import os
from collections.abc import Awaitable
from io import BytesIO
from typing import TYPE_CHECKING, Any

import httpx
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.file.base import get_default_fs
from llama_index.core.schema import Document
from pydantic import BaseModel
from pypdf import PdfReader
from pypdf.errors import PyPdfError
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from swiss_ai_hub.core.generative_ai.document.tables.markdown_table import wrap_markdown_tables
from swiss_ai_hub.core.generative_ai.utils.image_processor import embed_images_as_base64, extract_and_upload_images
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mineru.mineru_settings import MineruSettings
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    NUMBER_OF_PAGES,
)

if TYPE_CHECKING:
    from fsspec import AbstractFileSystem

logger = logging.getLogger(__name__)


class MineruTransientError(Exception):
    """Raised when MinerU API returns an error that can be retried."""


class MineruRequestError(Exception):
    """Raised when MinerU rejects a request for a reason retrying cannot fix."""


class MineruParseResponse(BaseModel):
    """Response schema from MinerU /file_parse endpoint."""

    backend: str
    version: str
    results: dict[str, dict[str, Any]]


class MineruFileResult(BaseModel):
    """Extracted per-file fields from one or more /file_parse responses."""

    backend: str
    version: str
    md_content: str
    num_pages: int
    images: dict[str, str]


class MineruLoader(BaseReader):
    """
    Document loader using MinerU's HTTP API.

    Communicates with MinerU exclusively via HTTP, ensuring complete AGPL
    license isolation. Supports PDF and image files with OCR, table detection,
    and formula extraction.
    """

    CONTENT_TYPE_MAP: dict[str, str] = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
        ".tiff": "image/tiff",
        ".jp2": "image/jp2",
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.config = MineruSettings()

    @trace_fn
    def load_data(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: "AbstractFileSystem | None" = None,
        include_images: bool = True,
    ) -> list[Document]:
        """Load and process document synchronously using MinerU API.

        Not supported in async contexts — use aload_data() instead.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise RuntimeError(
                "MineruLoader.load_data() cannot be called from within an existing async event loop. "
                "Use aload_data() instead."
            )
        return asyncio.run(self.aload_data(file, extra_info, fs, include_images))

    async def aload_data(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: "AbstractFileSystem | None" = None,
        include_images: bool = True,
    ) -> list[Document]:
        """Load and process document asynchronously using MinerU API."""
        fs = fs or get_default_fs()
        filename = os.path.basename(file)

        logger.debug(f"[MineruLoader] Starting async load for file: {filename}")

        file_bytes = await asyncio.to_thread(fs.cat_file, file)
        logger.debug(f"[MineruLoader] File read complete: {filename}, size: {len(file_bytes)} bytes")

        result = await self._convert_document(file_bytes, filename, include_images)
        logger.debug(f"[MineruLoader] Conversion complete for: {filename}")

        documents = await self._process_response(
            result=result,
            file=file,
            filename=filename,
            fs=fs,
            extra_info=extra_info,
            include_images=include_images,
        )

        logger.debug(f"[MineruLoader] Processing complete for: {filename}, returning {len(documents)} document(s)")
        return documents

    async def aload_data_from_bytes(
        self,
        content: bytes,
        filename: str,
        extra_info: dict | None = None,
        fs: "AbstractFileSystem | None" = None,
        include_images: bool = True,
        embed_base64: bool = False,
    ) -> list[Document]:
        """
        Load and process document from raw bytes.

        Used by the API layer when documents are uploaded directly rather than
        read from a filesystem.
        """
        if include_images and not embed_base64 and fs is None:
            raise ValueError(
                "Filesystem (fs) is required when include_images=True and embed_base64=False. "
                "Provide an S3 filesystem to store extracted images, or set embed_base64=True."
            )

        if fs is None:
            fs = get_default_fs()

        logger.debug(
            f"[MineruLoader] Processing from bytes: {filename}, {len(content)} bytes, embed_base64={embed_base64}"
        )

        result = await self._convert_document(content, filename, include_images=True)

        bucket_name = AIHubSettings().SHARED_BUCKET_NAME
        synthetic_file = f"{bucket_name}/api_uploads/{filename}"

        documents = await self._process_response(
            result=result,
            file=synthetic_file,
            filename=filename,
            fs=fs,
            extra_info=extra_info,
            include_images=include_images,
            embed_base64=embed_base64,
        )

        return documents

    async def _convert_document(
        self,
        file_bytes: bytes,
        filename: str,
        include_images: bool,
    ) -> MineruFileResult:
        """
        Convert a document via MinerU, splitting large PDFs into page batches.

        MinerU renders all requested pages into memory at once, so parsing a
        whole large PDF in one request OOMs the server regardless of file size.
        Page-range requests keep server memory constant per batch.
        """
        ext = os.path.splitext(filename)[1].lower()
        batch_size = self.config.PAGE_BATCH_SIZE
        if ext != ".pdf" or batch_size <= 0:
            return await self._convert_unbatched(file_bytes, filename, include_images)

        try:
            total_pages = await asyncio.to_thread(self._count_pdf_pages, file_bytes)
        except PyPdfError as e:
            logger.warning(f"[MineruLoader] Page-count probe failed for {filename}, parsing unbatched: {e}")
            return await self._convert_unbatched(file_bytes, filename, include_images)

        ranges = self._page_ranges(total_pages, batch_size)
        if len(ranges) <= 1:
            return await self._convert_unbatched(file_bytes, filename, include_images)
        return await self._convert_batched(file_bytes, filename, include_images, ranges, total_pages)

    async def _convert_unbatched(self, file_bytes: bytes, filename: str, include_images: bool) -> MineruFileResult:
        return await self._with_deadline(
            self._convert_batch(file_bytes, filename, include_images, None, None),
            num_batches=1,
            filename=filename,
        )

    async def _convert_batched(
        self,
        file_bytes: bytes,
        filename: str,
        include_images: bool,
        ranges: list[tuple[int, int]],
        total_pages: int,
    ) -> MineruFileResult:
        semaphore = asyncio.Semaphore(self.config.MAX_CONCURRENT_BATCH_REQUESTS)

        async def convert_range(start: int, end: int) -> MineruFileResult:
            async with semaphore:
                logger.info(f"[MineruLoader] {filename}: parsing pages {start + 1}-{end + 1} of {total_pages}")
                return await self._convert_batch(file_bytes, filename, include_images, start, end)

        async def convert_all() -> MineruFileResult:
            async with asyncio.TaskGroup() as task_group:
                tasks = []
                for start, end in ranges:
                    tasks.append(task_group.create_task(convert_range(start, end)))
            return self._merge_results([task.result() for task in tasks])

        return await self._with_deadline(convert_all(), num_batches=len(ranges), filename=filename)

    async def _with_deadline[T](self, awaitable: Awaitable[T], num_batches: int, filename: str) -> T:
        """Poison-document guard: the deadline scales with batch waves so a hung backend cannot stall a run forever."""
        deadline = self.config.API_TIMEOUT * math.ceil(num_batches / self.config.MAX_CONCURRENT_BATCH_REQUESTS)
        try:
            return await asyncio.wait_for(awaitable, timeout=deadline)
        except TimeoutError:
            raise TimeoutError(f"MinerU conversion timed out after {deadline}s for {filename} ({num_batches} batches)")

    @staticmethod
    def _count_pdf_pages(file_bytes: bytes) -> int:
        return len(PdfReader(BytesIO(file_bytes)).pages)

    @staticmethod
    def _page_ranges(total_pages: int, batch_size: int) -> list[tuple[int, int]]:
        return [(start, min(start + batch_size, total_pages) - 1) for start in range(0, total_pages, batch_size)]

    async def _convert_batch(
        self,
        file_bytes: bytes,
        filename: str,
        include_images: bool,
        start_page_id: int | None,
        end_page_id: int | None,
    ) -> MineruFileResult:
        """Call MinerU API for one page range (or the whole document), with retries."""
        async for attempt in AsyncRetrying(**self._retry_kwargs()):
            with attempt:
                response = await self._execute_conversion(
                    file_bytes, filename, include_images, start_page_id, end_page_id
                )
                return self._extract_file_result(response, filename)
        raise RuntimeError("Retry loop exited unexpectedly")

    async def _execute_conversion(
        self,
        file_bytes: bytes,
        filename: str,
        include_images: bool,
        start_page_id: int | None = None,
        end_page_id: int | None = None,
    ) -> MineruParseResponse:
        """Execute the conversion request to MinerU API."""
        ext = os.path.splitext(filename)[1].lower()
        content_type = self.CONTENT_TYPE_MAP.get(ext, "application/octet-stream")

        vlm_server_url = self.config.VLM_SERVER_URL.rstrip("/")
        vlm_headers = {}
        if self.config.VLM_SERVER_API_KEY.get_secret_value():
            vlm_headers["Authorization"] = f"Bearer {self.config.VLM_SERVER_API_KEY.get_secret_value()}"

        data = {
            "backend": "vlm-http-client",
            "server_url": f"{vlm_server_url}/v1/chat/completions",
            "model_name": self.config.VLM_NAME,
            "return_md": "true",
            "return_middle_json": "true",
            "return_images": str(include_images).lower(),
            "formula_enable": str(self.config.FORMULA_ENABLE).lower(),
            "table_enable": str(self.config.TABLE_ENABLE).lower(),
        }
        if start_page_id is not None:
            data["start_page_id"] = str(start_page_id)
        if end_page_id is not None:
            data["end_page_id"] = str(end_page_id)

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.config.API_TIMEOUT)) as client:
                logger.debug(f"[MineruLoader] Calling MinerU API for: {filename}")

                response = await client.post(
                    f"{self.config.API_BASE_URL}/file_parse",
                    files={"files": (filename, file_bytes, content_type)},
                    data=data,
                    headers=vlm_headers if vlm_headers else None,
                )

                self._raise_for_status(response, filename)
                return MineruParseResponse.model_validate(response.json())

        except httpx.HTTPError as e:
            logger.exception(f"[MineruLoader] HTTP error for {filename}: {type(e).__name__}: {e}")
            raise MineruTransientError(f"HTTP error: {type(e).__name__}: {e}") from e
        except OSError as e:
            logger.exception(f"[MineruLoader] Network error for {filename}: {type(e).__name__}: {e}")
            raise MineruTransientError(f"Network error: {type(e).__name__}: {e}") from e

    @staticmethod
    def _raise_for_status(response: httpx.Response, filename: str) -> None:
        """Only server-side failures are worth retrying; 4xx rejections are deterministic."""
        if response.status_code == 200:
            return
        logger.error(
            f"[MineruLoader] API request failed for {filename}: "
            f"status={response.status_code}, response={response.text}"
        )
        if response.status_code >= 500 or response.status_code == 429:
            raise MineruTransientError(f"MinerU API request failed with status {response.status_code}: {response.text}")
        raise MineruRequestError(f"MinerU API rejected the request with status {response.status_code}: {response.text}")

    @staticmethod
    def _extract_file_result(response: MineruParseResponse, filename: str) -> MineruFileResult:
        file_stem = os.path.splitext(filename)[0]

        file_result = response.results.get(file_stem, {})
        if not file_result:
            logger.warning(f"[MineruLoader] No result for stem '{file_stem}', falling back to filename '{filename}'")
            file_result = response.results.get(filename, {})

        if not file_result:
            logger.exception(
                f"[MineruLoader] No result found for {filename}. Available keys: {response.results.keys()}"
            )
            raise ValueError(f"No result found for {filename} in MinerU response")

        md_content = file_result.get("md_content", "")
        if not md_content:
            logger.warning(f"[MineruLoader] Empty markdown content for {filename}")

        middle_json_str = file_result.get("middle_json", "{}")
        middle_json = json.loads(middle_json_str) if middle_json_str else {}

        return MineruFileResult(
            backend=response.backend,
            version=response.version,
            md_content=md_content or "",
            num_pages=len(middle_json.get("pdf_info", [])),
            images=file_result.get("images", {}),
        )

    @staticmethod
    def _merge_results(results: list[MineruFileResult]) -> MineruFileResult:
        """Stitch page-batch results back together; batches arrive in page order."""
        return MineruFileResult(
            backend=results[0].backend,
            version=results[0].version,
            md_content="\n\n".join(result.md_content for result in results if result.md_content),
            num_pages=sum(result.num_pages for result in results),
            images={name: data for result in results for name, data in result.images.items()},
        )

    async def _process_response(
        self,
        result: MineruFileResult,
        file: str,
        filename: str,
        fs: "AbstractFileSystem",
        extra_info: dict | None,
        include_images: bool,
        embed_base64: bool = False,
    ) -> list[Document]:
        """Process the merged MinerU result into Document objects."""
        md_content = result.md_content
        images = result.images

        if include_images and images:
            if embed_base64:
                md_content = embed_images_as_base64(
                    markdown_content=md_content,
                    images=images,
                )
            else:
                md_content = await extract_and_upload_images(
                    markdown_content=md_content,
                    images=images,
                    fs=fs,
                    source_file=file,
                )

        md_content = wrap_markdown_tables(md_content)

        metadata = {
            NUMBER_OF_PAGES: result.num_pages,
            "backend": result.backend,
            "mineru_version": result.version,
        }

        if extra_info:
            metadata.update(extra_info)

        logger.debug(f"[MineruLoader] Processed {filename}: {result.num_pages} pages, {len(images)} images")

        return [Document(text=md_content, extra_info=metadata)]

    def _retry_kwargs(self) -> dict[str, Any]:
        """Return retry configuration for tenacity."""

        def log_retry(retry_state: RetryCallState) -> None:
            logger.warning(
                f"MinerU conversion failed (attempt {retry_state.attempt_number}), "
                f"retrying in {retry_state.next_action.sleep}s: {retry_state.outcome.exception()}"
            )

        return {
            "stop": stop_after_attempt(4),  # 3 retries + 1 initial attempt
            "wait": wait_exponential(multiplier=1, min=1, max=64),
            "retry": retry_if_exception_type(MineruTransientError),
            "before_sleep": log_retry,
            "reraise": True,
        }
