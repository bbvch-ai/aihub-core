"""
MinerU Document Loader - AGPL-Free Implementation.

Communicates with MinerU exclusively via HTTP API, ensuring complete
license isolation. MinerU handles PDF and image parsing with high-quality
OCR and document structure extraction.

The VLM (Vision Language Model) inference is routed through LiteLLM for
unified model routing and fallback support.
"""

import asyncio
import json
import logging
import os
import re
from typing import TYPE_CHECKING, Any

import httpx
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.file.base import get_default_fs
from llama_index.core.schema import Document
from pydantic import BaseModel
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from aihub_lib.generative_ai.document.tables.markdown_table import wrap_tables_with_tags
from aihub_lib.generative_ai.utils.image_processor import extract_and_upload_images
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.mineru.MineruSettings import MineruSettings
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.rag.vectors.node_metadata import (
    NUMBER_OF_PAGES,
)

if TYPE_CHECKING:
    from fsspec import AbstractFileSystem

logger = logging.getLogger(__name__)


class MineruTransientError(Exception):
    """Raised when MinerU API returns an error that can be retried."""

    pass


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

    ### Output Format
    Returns LlamaIndex Documents with:
    - Markdown text content
    - Images wrapped in `<figure>` tags with S3 paths
    - Tables wrapped in `<table>` tags
    - Metadata including page count
    """

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
        """Load and process document synchronously using MinerU API."""
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

        # Read file content
        file_bytes = await asyncio.to_thread(fs.cat_file, file)
        logger.debug(f"[MineruLoader] File read complete: {filename}, size: {len(file_bytes)} bytes")

        # Call MinerU API
        result = await self._convert_document(file_bytes, filename, include_images)
        logger.debug(f"[MineruLoader] Conversion complete for: {filename}")

        # Process response
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
    ) -> list[Document]:
        """
        Load and process document from raw bytes.

        Used by the API layer when documents are uploaded directly rather than
        read from a filesystem.

        ### Arguments
        - `content`: Raw bytes of the document
        - `filename`: Name of the file (used for extension detection and output paths)
        - `extra_info`: Additional metadata to include in the Document
        - `fs`: Filesystem for storing extracted images (required for image extraction)
        - `include_images`: Whether to extract and upload images

        ### Raises
        - `ValueError`: If `include_images` is True but no filesystem is provided
        """
        if include_images and fs is None:
            raise ValueError(
                "Filesystem (fs) is required when include_images=True. "
                "Provide an S3 filesystem to store extracted images."
            )

        # Use local filesystem only if images are not being extracted
        if fs is None:
            fs = get_default_fs()

        logger.debug(f"[MineruLoader] Processing from bytes: {filename}, size: {len(content)} bytes")

        # Call MinerU API
        result = await self._convert_document(content, filename, include_images)

        # For API usage without a source file path, we need a synthetic path
        # with S3 bucket prefix for figure storage
        bucket_name = AIHubSettings().SHARED_BUCKET_NAME
        synthetic_file = f"{bucket_name}/api_uploads/{filename}"

        # Process response
        documents = await self._process_response(
            result=result,
            file=synthetic_file,
            filename=filename,
            fs=fs,
            extra_info=extra_info,
            include_images=include_images,
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
        # Determine content type based on extension
        ext = os.path.splitext(filename)[1].lower()
        content_type_map = {
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
        content_type = content_type_map.get(ext, "application/octet-stream")

        # Build VLM server URL with authentication
        vlm_server_url = self.config.VL_SERVER_URL.rstrip("/")
        vlm_headers = {}
        if self.config.VL_API_KEY.get_secret_value():
            vlm_headers["Authorization"] = f"Bearer {self.config.VL_API_KEY.get_secret_value()}"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.config.API_TIMEOUT)) as client:
                logger.debug(f"[MineruLoader] Calling MinerU API for: {filename}")

                response = await client.post(
                    f"{self.config.API_BASE_URL}/file_parse",
                    files={"files": (filename, file_bytes, content_type)},
                    data={
                        "backend": "vlm-http-client",
                        "server_url": f"{vlm_server_url}/v1/chat/completions",
                        "model_name": self.config.VL_MODEL_NAME,
                        "return_md": "true",
                        "return_middle_json": "true",
                        "return_images": str(include_images).lower(),
                        "formula_enable": str(self.config.FORMULA_ENABLE).lower(),
                        "table_enable": str(self.config.TABLE_ENABLE).lower(),
                    },
                    headers=vlm_headers if vlm_headers else None,
                )

                if response.status_code != 200:
                    logger.error(
                        f"[MineruLoader] API request failed for {filename}: "
                        f"status={response.status_code}, response={response.text}"
                    )
                    raise MineruTransientError(
                        f"MinerU API request failed with status {response.status_code}: {response.text}"
                    )

                return MineruParseResponse.model_validate(response.json())

        except httpx.HTTPError as e:
            logger.error(f"[MineruLoader] HTTP error for {filename}: {type(e).__name__}: {e}")
            raise MineruTransientError(f"HTTP error: {type(e).__name__}: {e}") from e
        except OSError as e:
            logger.error(f"[MineruLoader] Network error for {filename}: {type(e).__name__}: {e}")
            raise MineruTransientError(f"Network error: {type(e).__name__}: {e}") from e

    async def _process_response(
        self,
        result: MineruParseResponse,
        file: str,
        filename: str,
        fs: "AbstractFileSystem",
        extra_info: dict | None,
        include_images: bool,
    ) -> list[Document]:
        """Process MinerU API response into Document objects."""
        # Get file stem (filename without extension) for result lookup
        file_stem = os.path.splitext(filename)[0]

        file_result = result.results.get(file_stem, {})
        if not file_result:
            # Try with full filename as fallback
            file_result = result.results.get(filename, {})

        if not file_result:
            logger.error(f"[MineruLoader] No result found for {filename}. Available keys: {result.results.keys()}")
            raise ValueError(f"No result found for {filename} in MinerU response")

        md_content = file_result.get("md_content", "")
        middle_json_str = file_result.get("middle_json", "{}")
        images = file_result.get("images", {})

        if not md_content:
            logger.warning(f"[MineruLoader] Empty markdown content for {filename}")

        # Parse middle_json for page count
        try:
            middle_json = json.loads(middle_json_str) if middle_json_str else {}
        except json.JSONDecodeError:
            middle_json = {}

        num_pages = len(middle_json.get("pdf_info", []))

        # Process images if included
        if include_images and images:
            md_content = await extract_and_upload_images(
                markdown_content=md_content,
                images=images,
                fs=fs,
                source_file=file,
            )

        # Wrap tables in <table> tags
        md_content = self._wrap_tables(md_content)

        # Build metadata
        metadata = {
            NUMBER_OF_PAGES: num_pages,
            "backend": result.backend,
            "mineru_version": result.version,
        }

        if extra_info:
            metadata.update(extra_info)

        logger.debug(f"[MineruLoader] Processed {filename}: {num_pages} pages, {len(images)} images")

        return [Document(text=md_content, extra_info=metadata)]

    def _wrap_tables(self, markdown_content: str) -> str:
        """
        Wrap markdown tables in <table> tags for downstream processing.

        Uses pattern matching to find markdown tables and wraps them with
        <table> tags so MarkdownStructuralNodeParser can identify them.
        """
        # Pattern to match markdown tables
        # Matches: |header|...\n|---|---|\n|row|...
        pattern = r"(\|[^\n]+\|\r?\n\|[:\-| ]+\|\r?(?:\n\|[^\n]+\|\r?)*)"

        tables = re.findall(pattern, markdown_content)

        for table in tables:
            wrapped = wrap_tables_with_tags([table])
            markdown_content = markdown_content.replace(table, wrapped, 1)

        return markdown_content

    def _retry_kwargs(self) -> dict:
        """Return retry configuration for tenacity."""

        def log_retry(retry_state) -> None:
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
