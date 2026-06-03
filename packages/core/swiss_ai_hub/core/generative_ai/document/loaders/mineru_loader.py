import asyncio
import json
import logging
import os
from typing import TYPE_CHECKING, Any

import httpx
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.file.base import get_default_fs
from llama_index.core.schema import Document
from pydantic import BaseModel
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


class MineruParseResponse(BaseModel):
    """Response schema from MinerU /file_parse endpoint."""

    backend: str
    version: str
    results: dict[str, dict[str, Any]]


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
        try:
            return await asyncio.wait_for(
                self._aload_data_impl(file, extra_info, fs, include_images),
                timeout=self.config.API_TIMEOUT,
            )
        except TimeoutError:
            raise TimeoutError(f"Document loading timed out after {self.config.API_TIMEOUT}s for: {file}")

    async def _aload_data_impl(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: "AbstractFileSystem | None" = None,
        include_images: bool = True,
    ) -> list[Document]:
        """Internal implementation of aload_data."""
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
    ) -> MineruParseResponse:
        """Call MinerU API to convert document."""
        async for attempt in AsyncRetrying(**self._retry_kwargs()):
            with attempt:
                return await self._execute_conversion(file_bytes, filename, include_images)
        raise RuntimeError("Retry loop exited unexpectedly")

    async def _execute_conversion(
        self,
        file_bytes: bytes,
        filename: str,
        include_images: bool,
    ) -> MineruParseResponse:
        """Execute the conversion request to MinerU API."""
        ext = os.path.splitext(filename)[1].lower()
        content_type = self.CONTENT_TYPE_MAP.get(ext, "application/octet-stream")

        vlm_server_url = self.config.VLM_SERVER_URL.rstrip("/")
        vlm_headers = {}
        if self.config.VLM_SERVER_API_KEY.get_secret_value():
            vlm_headers["Authorization"] = f"Bearer {self.config.VLM_SERVER_API_KEY.get_secret_value()}"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.config.API_TIMEOUT)) as client:
                logger.debug(f"[MineruLoader] Calling MinerU API for: {filename}")

                response = await client.post(
                    f"{self.config.API_BASE_URL}/file_parse",
                    files={"files": (filename, file_bytes, content_type)},
                    data={
                        "backend": "vlm-http-client",
                        "server_url": f"{vlm_server_url}/v1/chat/completions",
                        "model_name": self.config.VLM_NAME,
                        "return_md": "true",
                        "return_middle_json": "true",
                        "return_images": str(include_images).lower(),
                        "formula_enable": str(self.config.FORMULA_ENABLE).lower(),
                        "table_enable": str(self.config.TABLE_ENABLE).lower(),
                    },
                    headers=vlm_headers if vlm_headers else None,
                )

                if response.status_code != 200:
                    logger.exception(
                        f"[MineruLoader] API request failed for {filename}: "
                        f"status={response.status_code}, response={response.text}"
                    )
                    raise MineruTransientError(
                        f"MinerU API request failed with status {response.status_code}: {response.text}"
                    )

                return MineruParseResponse.model_validate(response.json())

        except httpx.HTTPError as e:
            logger.exception(f"[MineruLoader] HTTP error for {filename}: {type(e).__name__}: {e}")
            raise MineruTransientError(f"HTTP error: {type(e).__name__}: {e}") from e
        except OSError as e:
            logger.exception(f"[MineruLoader] Network error for {filename}: {type(e).__name__}: {e}")
            raise MineruTransientError(f"Network error: {type(e).__name__}: {e}") from e

    async def _process_response(
        self,
        result: MineruParseResponse,
        file: str,
        filename: str,
        fs: "AbstractFileSystem",
        extra_info: dict | None,
        include_images: bool,
        embed_base64: bool = False,
    ) -> list[Document]:
        """Process MinerU API response into Document objects."""
        file_stem = os.path.splitext(filename)[0]

        file_result = result.results.get(file_stem, {})
        if not file_result:
            logger.warning(f"[MineruLoader] No result for stem '{file_stem}', falling back to filename '{filename}'")
            file_result = result.results.get(filename, {})

        if not file_result:
            logger.exception(f"[MineruLoader] No result found for {filename}. Available keys: {result.results.keys()}")
            raise ValueError(f"No result found for {filename} in MinerU response")

        md_content = file_result.get("md_content", "")
        middle_json_str = file_result.get("middle_json", "{}")
        images = file_result.get("images", {})

        if not md_content:
            logger.warning(f"[MineruLoader] Empty markdown content for {filename}")

        middle_json = json.loads(middle_json_str) if middle_json_str else {}
        num_pages = len(middle_json.get("pdf_info", []))

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
            NUMBER_OF_PAGES: num_pages,
            "backend": result.backend,
            "mineru_version": result.version,
        }

        if extra_info:
            metadata.update(extra_info)

        logger.debug(f"[MineruLoader] Processed {filename}: {num_pages} pages, {len(images)} images")

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
