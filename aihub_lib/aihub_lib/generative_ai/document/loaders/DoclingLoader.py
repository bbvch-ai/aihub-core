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
        include_images = include_images if include_images is not None else True

        fs = fs or get_default_fs()
        encoded_string = await asyncio.to_thread(self._read_file_sync, fs, file)
        file_name = os.path.basename(file)

        answer = await self.convert_document_async(encoded_string, file_name, include_images)
        return await asyncio.to_thread(
            self._process_docling_response, answer=answer, file=file, fs=fs, extra_info=extra_info
        )

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
                        "url": f"{self.config.HOSTED_VLM_API_BASE_URL}/v1/chat/completions",
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

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers including Authorization if API key is configured."""
        headers = {"Content-Type": "application/json"}
        if self.config.API_KEY:
            headers["X-Api-Key"] = f"{self.config.API_KEY}"
        return headers

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
            with httpx.Client(timeout=self.config.API_TIMEOUT) as client:
                response = client.post(
                    f"{self.config.API_BASE_URL}/v1/convert/source",
                    json=request_body,
                    headers=self._build_headers(),
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
        request_body = self._build_request_body(file_content, filename, include_images, to_formats)
        async for attempt in AsyncRetrying(**self._retry_kwargs()):
            with attempt:
                return await self._execute_async_conversion(request_body)
        raise RuntimeError("Retry loop exited unexpectedly")

    async def _execute_async_conversion(self, request_body: dict) -> dict:
        """Execute the async conversion request and poll for completion."""
        try:
            async with httpx.AsyncClient(timeout=self.config.API_TIMEOUT) as client:
                response = await client.post(
                    f"{self.config.API_BASE_URL}/v1/convert/source/async",
                    json=request_body,
                    headers=self._build_headers(),
                )

                if response.status_code != 200:
                    raise DoclingTransientError(
                        f"Docling async API request failed with status code {response.status_code}: {response.text}"
                    )

                job_response = response.json()
                if not job_response or "task_id" not in job_response:
                    raise DoclingTransientError(f"Docling API returned invalid job response: {job_response}")

                task_id = job_response["task_id"]
                return await self._poll_job_completion(client, task_id)
        except (httpx.ReadError, httpx.ConnectError, httpx.TimeoutException) as e:
            raise DoclingTransientError(f"Network error: {e}") from e

    async def _poll_job_completion(self, client: httpx.AsyncClient, task_id: str) -> dict:
        """Poll the task status until completion and return the result."""
        for _ in range(self.config.MAX_POLLS):
            status_response = await client.get(
                f"{self.config.API_BASE_URL}/v1/status/poll/{task_id}",
                headers=self._build_headers(),
            )

            if status_response.status_code != 200:
                raise DoclingTransientError(
                    f"Docling task status request failed with status code {status_response.status_code}: "
                    f"{status_response.text}"
                )

            task_status = status_response.json()

            if not task_status or "task_status" not in task_status:
                raise DoclingTransientError(f"Docling API returned invalid response: {task_status}")

            if task_status["task_status"] == "success":
                result_response = await client.get(
                    f"{self.config.API_BASE_URL}/v1/result/{task_id}",
                    headers=self._build_headers(),
                )

                if result_response.status_code != 200:
                    raise DoclingTransientError(
                        f"Docling result request failed with status code {result_response.status_code}: "
                        f"{result_response.text}"
                    )

                return result_response.json()

            elif task_status["task_status"] == "failure":
                # Note: docling-serve does not currently expose failure reasons in the API
                # See: https://github.com/docling-project/docling-serve/issues/365
                raise DoclingTransientError(f"Docling conversion task {task_id} failed. Full response: {task_status}")
            elif task_status["task_status"] in ["pending", "started"]:
                await asyncio.sleep(self.config.POLL_INTERVAL)
            elif task_status["task_status"] == "skipped":
                raise DoclingTransientError(
                    f"Docling conversion task {task_id} was skipped. Full response: {task_status}"
                )
            else:
                raise DoclingTransientError(f"Unknown task status: {task_status['task_status']}")

        raise TimeoutError(f"Docling conversion task {task_id} did not complete within the timeout period")


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
