import asyncio
import base64
import html
import os
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup
from docling_core.types import DoclingDocument
from docling_core.types.doc import ImageRefMode
from fsspec import AbstractFileSystem
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.file.base import get_default_fs
from llama_index.core.schema import Document

from aihub_lib.generative_ai.utils.path_utils import create_figures_folder_name
from aihub_lib.infrastructure.docling.DoclingSettings import DoclingSettings
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.rag.vectors.node_metadata import (
    NODE_CONTENT_TYPE_FIGURE,
    NODE_CONTENT_TYPE_TABLE,
    NUMBER_OF_PAGES,
)


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
        figures_directory_name: str | None = None,
        include_images: bool | None = None,
    ) -> list[Document]:
        """Load and process documents synchronously using the Docling service."""
        include_images = include_images if include_images is not None else True

        fs = fs or get_default_fs()
        with fs.open(file, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read()).decode("utf-8")
        file_name = os.path.basename(file)

        answer = self.convert_document(encoded_string, file_name, include_images)
        return self._process_docling_response(answer, file, extra_info, fs, figures_directory_name)

    async def aload_data(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: AbstractFileSystem | None = None,
        figures_directory_name: str | None = None,
        include_images: bool | None = None,
    ) -> list[Document]:
        """Load and process documents asynchronously using the Docling service."""
        include_images = include_images if include_images is not None else True

        fs = fs or get_default_fs()
        with fs.open(file, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read()).decode("utf-8")
        file_name = os.path.basename(file)

        answer = await self.convert_document_async(encoded_string, file_name, include_images)
        return self._process_docling_response(answer, file, extra_info, fs, figures_directory_name)

    def _process_docling_response(
        self,
        answer: dict,
        file: str,
        extra_info: dict | None = None,
        fs: AbstractFileSystem | None = None,
        figures_directory_name: str | None = None,
    ) -> list[Document]:
        """Process the Docling API response into Document objects."""
        doc = DoclingDocument(**answer["document"]["json_content"])
        markdown_content = doc.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)

        if len(doc.pictures) > 0:
            img_strs = [picture.export_to_markdown(doc) for picture in doc.pictures]
            markdown_content = inject_table_tags(inject_figure_tags(markdown_content, img_strs))
        else:
            markdown_content = inject_table_tags(markdown_content)

        metadata = {NUMBER_OF_PAGES: len(answer["document"]["json_content"]["pages"])}

        soup = BeautifulSoup(markdown_content, "html.parser")
        figure_tags = soup.find_all("figure")

        figures_dir = create_figures_folder_name(file, figures_directory_name)
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
    def _build_request_body(self, file_content: str, filename: str, include_images: bool) -> dict:
        """Build the request body for the Docling VLM Pipeline."""
        return {
            "options": {
                "to_formats": self.config.TO_FORMATS,
                "include_images": include_images,
                "pipeline": "vlm",
                "vlm_pipeline_model_api": {
                    "url": f"{self.config.HOSTED_VLM_API_ENDPOINT}/v1/chat/completions",
                    "params": {
                        "model": self.config.VLM_MODEL_NAME,
                        "max_tokens": 8196,
                        "skip_special_tokens": False,
                    },
                    "response_format": "doctags",
                    "headers": {"Authorization": f"Bearer {self.config.HOSTED_VLM_API_KEY}"},
                },
            },
            "sources": [{"base64_string": file_content, "filename": filename, "kind": "file"}],
        }

    def convert_document(self, file_content: str, filename: str, include_images: bool) -> dict:
        request_body = self._build_request_body(file_content, filename, include_images)

        response = httpx.post(
            f"{self.config.API_ENDPOINT}/v1/convert/source",
            json=request_body,
            headers={"Content-Type": "application/json"},
            timeout=self.config.API_TIMEOUT,
        )

        if response.status_code != 200:
            raise ValueError(
                f"Docling sync API request failed with status code {response.status_code}: {response.text}"
            )

        return response.json()

    async def convert_document_async(self, file_content: str, filename: str, include_images: bool) -> dict:
        request_body = self._build_request_body(file_content, filename, include_images)

        async with httpx.AsyncClient(timeout=self.config.API_TIMEOUT) as client:
            response = await client.post(
                f"{self.config.API_ENDPOINT}/v1/convert/source/async",
                json=request_body,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                raise ValueError(
                    f"Docling async API request failed with status code {response.status_code}: {response.text}"
                )

            job_response = response.json()
            task_id = job_response["task_id"]

            return await self._poll_job_completion(client, task_id)

    async def _poll_job_completion(self, client: httpx.AsyncClient, task_id: str) -> dict:
        """Poll the task status until completion and return the result."""
        for _ in range(self.config.MAX_POLLS):
            status_response = await client.get(
                f"{self.config.API_ENDPOINT}/v1/status/poll/{task_id}",
                headers={"Content-Type": "application/json"},
            )

            if status_response.status_code != 200:
                raise ValueError(
                    f"Docling task status request failed with status code {status_response.status_code}: "
                    f"{status_response.text}"
                )

            task_status = status_response.json()

            if task_status["task_status"] == "success":
                result_response = await client.get(
                    f"{self.config.API_ENDPOINT}/v1/result/{task_id}",
                    headers={"Content-Type": "application/json"},
                )

                if result_response.status_code != 200:
                    raise ValueError(
                        f"Docling result request failed with status code {result_response.status_code}: "
                        f"{result_response.text}"
                    )

                return result_response.json()

            elif task_status["task_status"] == "failure":
                raise ValueError(
                    f"Docling conversion task failed: {task_status.get('task_meta', {}).get('error', 'Unknown error')}"
                )
            elif task_status["task_status"] in ["pending", "started"]:
                await asyncio.sleep(self.config.POLL_INTERVAL)
            elif task_status["task_status"] == "skipped":
                raise ValueError(
                    f"Docling conversion task was skipped: "
                    f"{task_status.get('task_meta', {}).get('reason', 'Unknown reason')}"
                )
            else:
                raise ValueError(f"Unknown task status: {task_status['task_status']}")

        raise TimeoutError(f"Docling conversion task {task_id} did not complete within the timeout period")


def inject_figure_tags(markdown_text: str, img_strs: list[str]):
    """Inject html <figure> tags around base64 encoded images."""
    for image_str in img_strs:
        markdown_text = markdown_text.replace(
            image_str, f"<{NODE_CONTENT_TYPE_FIGURE}>{image_str}</{NODE_CONTENT_TYPE_FIGURE}>"
        )
    return markdown_text


def inject_table_tags(markdown_text: str):
    """Inject html <table> tags around Markdown tables."""
    pattern = r"(\|[^\n]+\|\r?\n\|[:\-| ]+\|\r?(?:\n\|[^\n]+\|\r?)*)"
    markdown_text = re.sub(pattern, f"<{NODE_CONTENT_TYPE_TABLE}>\\1</{NODE_CONTENT_TYPE_TABLE}>", markdown_text)

    return markdown_text
