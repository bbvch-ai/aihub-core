import asyncio
import base64
import html
import logging
import os
import re
from io import BytesIO
from typing import Annotated, Any

import httpx
from bs4 import BeautifulSoup
from docling_core.types import DoclingDocument
from docling_core.types.doc import ImageRefMode, TableItem
from fsspec import AbstractFileSystem
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.file.base import get_default_fs
from llama_index.core.schema import Document
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError, PdfStreamError
from pypdf.generic import RectangleObject
from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from aihub_lib.generative_ai.document.tables.markdown_table import create_markdown_table, wrap_tables_with_tags
from aihub_lib.generative_ai.utils.path_utils import create_figures_folder_name
from aihub_lib.infrastructure.docling.DoclingSettings import DoclingSettings, PipelineType
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.rag.vectors.node_metadata import (
    NODE_CONTENT_TYPE_FIGURE,
    NUMBER_OF_PAGES,
)

logger = logging.getLogger(__name__)

# A4 page dimensions in PostScript points (72 points = 1 inch)
# 210mm × 297mm ≈ 595pt × 842pt
# Used as fallback when PDF pages have missing/invalid mediabox
A4_WIDTH_POINTS = 595
A4_HEIGHT_POINTS = 842


def _fix_pdf_mediabox(
    content: Annotated[bytes, "Raw PDF file content"],
    filename: Annotated[str, "Original filename for extension check and logging"],
) -> bytes:
    """
    Preprocess PDF files to fix missing or invalid page dimensions.

    ### Why This Fix?
    Some PDF generators (notably certain scanners and legacy export tools) create
    pages without proper mediabox definitions. Docling's PDF parser fails on such
    files with dimension-related errors. This function detects and repairs these
    malformed PDFs before conversion.

    ### Invalid MediaBox Conditions
    - `mediabox is None`: Page has no dimension metadata
    - `width == 0` or `height == 0`: Degenerate page dimensions

    ### Why A4 Fallback?
    A4 (210×297mm) is the ISO standard and most common paper size globally,
    making it a reasonable default for documents with unknown dimensions.

    ### Graceful Degradation
    If PDF processing fails, original content is returned unchanged to allow
    downstream processing to attempt conversion or report errors appropriately.
    """
    if not filename.lower().endswith(".pdf"):
        return content

    try:
        reader = PdfReader(BytesIO(content))
        writer = PdfWriter()

        for page in reader.pages:
            if page.mediabox is None or page.mediabox.width == 0 or page.mediabox.height == 0:
                page.mediabox = RectangleObject((0, 0, A4_WIDTH_POINTS, A4_HEIGHT_POINTS))
            writer.add_page(page)

        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    except (PdfReadError, PdfStreamError) as e:
        logger.warning(f"Could not preprocess PDF {filename}: {e}")
        return content


class DoclingTransientError(Exception):
    """Raised when Docling API returns an error that can be retried."""

    pass


class DoclingLoader(BaseReader):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.config = DoclingSettings()

    @trace_fn
    def load_data(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: AbstractFileSystem | None = None,
        include_images: bool | None = None,
    ) -> list[Document]:
        """Load and process documents synchronously using the Docling service."""
        include_images = include_images if include_images is not None else True

        fs = fs or get_default_fs()
        encoded_string = self._read_file_sync(fs, file)
        file_name = os.path.basename(file)

        answer = self.convert_document(encoded_string, file_name, include_images)
        return self._process_docling_response(answer=answer, file=file, extra_info=extra_info, fs=fs)

    async def aload_data(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: AbstractFileSystem | None = None,
        include_images: bool | None = None,
    ) -> list[Document]:
        """Load and process documents asynchronously using the Docling service."""
        try:
            return await asyncio.wait_for(
                self._aload_data_impl(file, extra_info, fs, include_images),
                timeout=self.config.OPERATION_TIMEOUT,
            )
        except TimeoutError:
            raise TimeoutError(f"Document loading timed out after {self.config.OPERATION_TIMEOUT}s for: {file}")

    async def _aload_data_impl(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: AbstractFileSystem | None = None,
        include_images: bool | None = None,
    ) -> list[Document]:
        """Internal implementation of aload_data with actual processing logic."""
        include_images = include_images if include_images is not None else True

        fs = fs or get_default_fs()
        file_name = os.path.basename(file)
        logger.debug(f"[DoclingLoader] Starting async load for file: {file_name}")

        encoded_string = await asyncio.to_thread(self._read_file_sync, fs, file)
        logger.debug(f"[DoclingLoader] File read complete for: {file_name}, encoded size: {len(encoded_string)} bytes")

        answer = await self.convert_document_async(encoded_string, file_name, include_images)
        logger.debug(f"[DoclingLoader] Conversion complete for: {file_name}, processing response")

        result = await asyncio.to_thread(
            self._process_docling_response, answer=answer, file=file, fs=fs, extra_info=extra_info
        )
        logger.debug(f"[DoclingLoader] Processing complete for: {file_name}, returning {len(result)} document(s)")
        return result

    def _read_file_sync(self, fs: AbstractFileSystem, file: str) -> str:
        file_content = fs.cat_file(file)
        file_content = _fix_pdf_mediabox(file_content, file)
        return base64.b64encode(file_content).decode("utf-8")

    def _process_docling_response(
        self,
        answer: dict,
        file: str,
        fs: AbstractFileSystem,
        extra_info: dict | None = None,
    ) -> list[Document]:
        """Process the Docling API response into Document objects."""
        json_content = answer["document"]["json_content"]
        _fix_null_meta_fields(json_content)
        doc = DoclingDocument(**json_content)
        markdown_content = doc.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)

        if len(doc.pictures) > 0:
            img_strs = [picture.export_to_markdown(doc) for picture in doc.pictures]
            markdown_content = inject_figure_tags(markdown_text=markdown_content, img_strs=img_strs)

        markdown_content = convert_tables_to_markdown(markdown_text=markdown_content, tables=doc.tables)

        metadata = {NUMBER_OF_PAGES: len(answer["document"]["json_content"]["pages"])}

        soup = BeautifulSoup(markdown_content, "html.parser")
        figure_tags = soup.find_all("figure")

        figures_dir = create_figures_folder_name(file)
        for idx, figure_tag in enumerate(figure_tags):
            encoded_figure = figure_tag.text.split("](")[1][:-1]
            encoded_figure = encoded_figure.replace("data:image/png;base64,", "")
            figure_bytes = base64.b64decode(encoded_figure)

            blob_path = os.path.join(figures_dir, f"figure_{idx + 1}.png")
            with fs.open(blob_path, "wb") as pdf_file:
                pdf_file.write(figure_bytes)

            markdown_figure = f"![Figure {idx + 1}]({blob_path})"
            figure_tag.replace_with(f"<{NODE_CONTENT_TYPE_FIGURE}>{markdown_figure}</{NODE_CONTENT_TYPE_FIGURE}>")

        return [
            Document(
                text=html.unescape(str(soup)),
                extra_info={**extra_info, **metadata} if extra_info else metadata,
            )
        ]

    @trace_fn
    def _build_request_body(
        self, file_content: str, filename: str, include_images: bool, to_formats: list[str] | None = None
    ) -> dict:
        """Build the request body for the Docling VLM Pipeline."""
        if self.config.PIPELINE_TYPE == PipelineType.STANDARD:
            return {
                "options": {
                    "to_formats": to_formats if to_formats is not None else self.config.TO_FORMATS,
                    "image_export_mode": self.config.IMAGE_EXPORT_MODE,
                    "do_ocr": self.config.DO_OCR,
                    "force_ocr": self.config.FORCE_OCR,
                    "ocr_engine": self.config.OCR_ENGINE,
                    "pdf_backend": self.config.PDF_BACKEND,
                    "table_mode": self.config.TABLE_MODE,
                    "abort_on_error": False,
                    "do_table_structure": True,
                    "include_images": include_images,
                    "images_scale": self.config.IMAGES_SCALE,
                    "do_code_enrichment": True,
                    "do_formula_enrichment": True,
                    "do_picture_classification": False,
                    "do_picture_description": False,
                    "md_page_break_placeholder": self.config.MD_PAGE_BREAK_PLACEHOLDER,
                },
                "sources": [{"base64_string": file_content, "filename": filename, "kind": "file"}],
            }

        elif self.config.PIPELINE_TYPE == PipelineType.VLM:
            return {
                "options": {
                    "to_formats": to_formats if to_formats is not None else self.config.TO_FORMATS,
                    "include_images": include_images,
                    "pipeline": "vlm",
                    "vlm_pipeline_model_api": {
                        "url": f"{self.config.HOSTED_VLM_API_ENDPOINT}/v1/chat/completions",
                        "params": {
                            "model": self.config.VLM_MODEL_NAME,
                            "max_tokens": 8176,  # 8192 (max tokens) - 16 (for docling)
                            "skip_special_tokens": False,
                        },
                        "response_format": "doctags",
                        "headers": {"Authorization": f"Bearer {self.config.HOSTED_VLM_API_KEY}"},
                    },
                },
                "sources": [{"base64_string": file_content, "filename": filename, "kind": "file"}],
            }

        raise ValueError(f"Unsupported pipeline type: {self.config.PIPELINE_TYPE}")

    def _retry_kwargs(self) -> dict:
        """Return retry configuration for tenacity."""

        def log_retry(retry_state) -> None:
            logger.warning(
                f"Docling conversion failed (attempt {retry_state.attempt_number}), "
                f"retrying in {retry_state.next_action.sleep}s: {retry_state.outcome.exception()}"
            )

        return {
            "stop": stop_after_attempt(self.config.HTTP_RETRIES + 1),
            "wait": wait_exponential(multiplier=1, min=1, max=64),
            "retry": retry_if_exception_type(DoclingTransientError),
            "before_sleep": log_retry,
            "reraise": True,
        }

    def _get_httpx_timeout(self) -> httpx.Timeout:
        """Return httpx timeout configuration with explicit values for each phase."""
        return httpx.Timeout(
            connect=30.0,  # Connection establishment
            read=float(self.config.API_TIMEOUT),  # Reading response
            write=60.0,  # Writing request body (large files)
            pool=10.0,  # Waiting for connection from pool
        )

    def convert_document(
        self, file_content: str, filename: str, include_images: bool, to_formats: list[str] | None = None
    ) -> dict:
        request_body = self._build_request_body(file_content, filename, include_images, to_formats)
        for attempt in Retrying(**self._retry_kwargs()):
            with attempt:
                return self._execute_sync_conversion(request_body)
        raise RuntimeError("Retry loop exited unexpectedly")

    def _execute_sync_conversion(self, request_body: dict) -> dict:
        """Execute the sync conversion request."""
        try:
            with httpx.Client(timeout=self._get_httpx_timeout()) as client:
                response = client.post(
                    f"{self.config.BASE_API_URL}/v1/convert/source",
                    json=request_body,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code != 200:
                    raise DoclingTransientError(
                        f"Docling sync API request failed with status code {response.status_code}: {response.text}"
                    )

                return response.json()
        except (httpx.ReadError, httpx.ConnectError, httpx.TimeoutException) as e:
            raise DoclingTransientError(f"Network error: {e}") from e

    async def convert_document_async(
        self,
        file_content: str,
        filename: str,
        include_images: bool,
        to_formats: list[str] | None = None,
    ) -> dict:
        logger.debug(
            f"[DoclingLoader] Starting async conversion for: {filename}, "
            f"pipeline: {self.config.PIPELINE_TYPE}, max_polls: {self.config.MAX_POLLS}, "
            f"poll_interval: {self.config.POLL_INTERVAL}s"
        )
        request_body = self._build_request_body(file_content, filename, include_images, to_formats)
        async for attempt in AsyncRetrying(**self._retry_kwargs()):
            with attempt:
                return await self._execute_async_conversion(request_body, filename)
        raise RuntimeError("Retry loop exited unexpectedly")

    async def _execute_async_conversion(self, request_body: dict, filename: str = "unknown") -> dict:
        """Execute the async conversion request and poll for completion."""
        try:
            async with httpx.AsyncClient(timeout=self._get_httpx_timeout()) as client:
                logger.debug(f"[DoclingLoader] Submitting async job to {self.config.BASE_API_URL} for: {filename}")
                response = await client.post(
                    f"{self.config.BASE_API_URL}/v1/convert/source/async",
                    json=request_body,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code != 200:
                    logger.error(
                        f"[DoclingLoader] Job submission failed for {filename}: "
                        f"status={response.status_code}, response={response.text}"
                    )
                    raise DoclingTransientError(
                        f"Docling async API request failed with status code {response.status_code}: {response.text}"
                    )

                job_response = response.json()
                if not job_response or "task_id" not in job_response:
                    logger.error(f"[DoclingLoader] Invalid job response for {filename}: {job_response}")
                    raise DoclingTransientError(f"Docling API returned invalid job response: {job_response}")

                task_id = job_response["task_id"]
                logger.debug(f"[DoclingLoader] Job submitted successfully for {filename}, task_id={task_id}")
                return await self._poll_job_completion(client, task_id, filename)
        except DoclingTransientError:
            raise
        except httpx.HTTPError as e:
            # Catch all httpx errors (connection reset, protocol errors, timeouts, etc.)
            # This handles docling restarts mid-conversion
            logger.error(f"[DoclingLoader] HTTP error for {filename}: {type(e).__name__}: {e}")
            raise DoclingTransientError(f"HTTP error: {type(e).__name__}: {e}") from e
        except OSError as e:
            # Catch OS-level network errors (connection refused, etc.)
            logger.error(f"[DoclingLoader] Network error for {filename}: {type(e).__name__}: {e}")
            raise DoclingTransientError(f"Network error: {type(e).__name__}: {e}") from e

    async def _poll_job_completion(self, client: httpx.AsyncClient, task_id: str, filename: str = "unknown") -> dict:
        """Poll the task status until completion and return the result."""
        logger.debug(
            f"[DoclingLoader] Starting polling for task_id={task_id}, file={filename}, "
            f"max_polls={self.config.MAX_POLLS}, interval={self.config.POLL_INTERVAL}s"
        )

        for poll_count in range(1, self.config.MAX_POLLS + 1):
            logger.debug(
                f"[DoclingLoader] Poll {poll_count}/{self.config.MAX_POLLS} for task_id={task_id}, file={filename}"
            )

            try:
                status_response = await client.get(
                    f"{self.config.BASE_API_URL}/v1/status/poll/{task_id}",
                    headers={"Content-Type": "application/json"},
                )
            except (httpx.HTTPError, OSError, asyncio.CancelledError) as e:
                logger.error(
                    f"[DoclingLoader] Poll {poll_count} failed for task_id={task_id}, "
                    f"file={filename}: {type(e).__name__}: {e}"
                )
                raise

            if status_response.status_code != 200:
                logger.error(
                    f"[DoclingLoader] Poll {poll_count} returned non-200 status for task_id={task_id}, "
                    f"file={filename}: status={status_response.status_code}, response={status_response.text}"
                )
                raise DoclingTransientError(
                    f"Docling task status request failed with status code {status_response.status_code}: "
                    f"{status_response.text}"
                )

            task_status = status_response.json()

            if not task_status or "task_status" not in task_status:
                logger.error(
                    f"[DoclingLoader] Poll {poll_count} returned invalid response for task_id={task_id}, "
                    f"file={filename}: {task_status}"
                )
                raise DoclingTransientError(f"Docling API returned invalid response: {task_status}")

            status_value = task_status["task_status"]
            logger.debug(
                f"[DoclingLoader] Poll {poll_count} status for task_id={task_id}, file={filename}: {status_value}"
            )

            if status_value == "success":
                logger.debug(
                    f"[DoclingLoader] Task completed successfully after {poll_count} poll(s) "
                    f"for task_id={task_id}, file={filename}. Fetching result..."
                )
                result_response = await client.get(
                    f"{self.config.BASE_API_URL}/v1/result/{task_id}",
                    headers={"Content-Type": "application/json"},
                )

                if result_response.status_code != 200:
                    logger.error(
                        f"[DoclingLoader] Failed to fetch result for task_id={task_id}, file={filename}: "
                        f"status={result_response.status_code}, response={result_response.text}"
                    )
                    raise DoclingTransientError(
                        f"Docling result request failed with status code {result_response.status_code}: "
                        f"{result_response.text}"
                    )

                result = result_response.json()
                logger.debug(f"[DoclingLoader] Result fetched successfully for task_id={task_id}, file={filename}")
                await self._clear_document(client, task_id)
                return result

            elif status_value == "failure":
                logger.error(
                    f"[DoclingLoader] Task failed for task_id={task_id}, file={filename}. "
                    f"Full response: {task_status}"
                )
                # Note: docling-serve does not currently expose failure reasons in the API
                # See: https://github.com/docling-project/docling-serve/issues/365
                raise DoclingTransientError(f"Docling conversion task {task_id} failed. Full response: {task_status}")

            elif status_value in ["pending", "started"]:
                logger.debug(
                    f"[DoclingLoader] Task still {status_value} for task_id={task_id}, file={filename}. "
                    f"Sleeping {self.config.POLL_INTERVAL}s before next poll..."
                )
                await asyncio.sleep(self.config.POLL_INTERVAL)

            elif status_value == "skipped":
                logger.error(
                    f"[DoclingLoader] Task was skipped for task_id={task_id}, file={filename}. "
                    f"Full response: {task_status}"
                )
                raise DoclingTransientError(
                    f"Docling conversion task {task_id} was skipped. Full response: {task_status}"
                )
            else:
                logger.error(
                    f"[DoclingLoader] Unknown task status '{status_value}' for task_id={task_id}, file={filename}"
                )
                raise DoclingTransientError(f"Unknown task status: {status_value}")

        logger.error(
            f"[DoclingLoader] Timeout after {self.config.MAX_POLLS} polls for task_id={task_id}, file={filename}. "
            f"Total wait time: {self.config.MAX_POLLS * self.config.POLL_INTERVAL}s"
        )
        raise TimeoutError(f"Docling conversion task {task_id} did not complete within the timeout period")

    async def _clear_document(self, client: httpx.AsyncClient, task_id: str) -> None:
        """
        Clear old results from the Docling server after retrieval.

        Uses GET /v1/clear/results?older_than=N to clear results older than
        CLEAR_RESULTS_DELAY seconds. This provides a safety buffer to avoid
        clearing results that may still be in use, while still cleaning up
        orphaned results from previous failed runs.
        """
        delay = self.config.CLEAR_RESULTS_DELAY
        try:
            response = await client.get(
                f"{self.config.BASE_API_URL}/v1/clear/results",
                params={"older_than": delay},
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                logger.debug(f"[DoclingLoader] Cleared old results (>{delay}s) after task_id={task_id}")
            else:
                logger.debug(
                    f"[DoclingLoader] Clear results returned status={response.status_code} "
                    f"after task_id={task_id}, response={response.text}"
                )
        except Exception as e:
            # Non-fatal: server will auto-cleanup eventually via SINGLE_USE_RESULTS
            logger.debug(f"[DoclingLoader] Clear results failed after task_id={task_id}: {e}")


def inject_figure_tags(markdown_text: str, img_strs: list[str]):
    """Inject html <figure> tags around base64 encoded images."""
    for image_str in img_strs:
        markdown_text = markdown_text.replace(
            image_str, f"<{NODE_CONTENT_TYPE_FIGURE}>{image_str}</{NODE_CONTENT_TYPE_FIGURE}>"
        )
    return markdown_text


def convert_tables_to_markdown(markdown_text: str, tables: list[TableItem]) -> str:
    """
    Replace Docling markdown tables with properly formatted markdown tables wrapped in <table> tags.

    Uses shared table utilities from aihub_lib.generative_ai.document.tables to ensure
    consistent table handling between document creation and node parsing.

    Tables are wrapped in <table> tags so MarkdownStructuralNodeParser can identify them.
    """
    pattern = r"(\|[^\n]+\|\r?\n\|[:\-| ]+\|\r?(?:\n\|[^\n]+\|\r?)*)"
    md_tables = re.findall(pattern, markdown_text)
    for md_table, table in zip(md_tables, tables):
        df = table.export_to_dataframe()
        formatted_tables = create_markdown_table(df)

        # create_markdown_table may return multiple tables separated by \n\n if merged tables were detected
        individual_tables = formatted_tables.split("\n\n")
        wrapped_tables = wrap_tables_with_tags(individual_tables)

        markdown_text = markdown_text.replace(md_table, wrapped_tables, 1)
    return markdown_text


def _fix_null_meta_fields(data: dict | list | Any) -> None:
    """Recursively fix null meta fields in Docling JSON content.

    Works around a bug in docling-core < 2.51.0 where _migrate_annotations_to_meta
    validator uses setdefault() on meta, which fails when meta is null. Fixed
    upstream in v2.51.0 (#417), but kept for compatibility with older docling-serve
    deployments that may return documents with null meta fields.
    """
    if isinstance(data, dict):
        if "meta" in data and data["meta"] is None:
            data["meta"] = {}
        for value in data.values():
            _fix_null_meta_fields(value)
    elif isinstance(data, list):
        for item in data:
            _fix_null_meta_fields(item)
