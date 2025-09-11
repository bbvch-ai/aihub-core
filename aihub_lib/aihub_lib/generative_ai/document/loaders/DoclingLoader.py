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
from aihub_lib.persistence.rag.vectors.node_metadata import (
    NODE_CONTENT_TYPE_FIGURE,
    NODE_CONTENT_TYPE_TABLE,
    NUMBER_OF_PAGES,
)


class DoclingLoader(BaseReader):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.config = DoclingSettings()

    def load_data(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: AbstractFileSystem | None = None,
        figures_directory_name: str | None = None,
        include_images: bool | None = None,
    ) -> list[Document]:
        fs = fs or get_default_fs()
        with fs.open(file, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read()).decode("utf-8")
        file_name = os.path.basename(file)

        answer = self.convert_document(encoded_string, file_name, include_images)
        doc = DoclingDocument(**answer["document"]["json_content"])
        markdown_content = doc.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
        if len(doc.pictures) > 0:
            img_strs = [
                f"![Image](data:image/png;base64,{picture._image_to_base64(picture.get_image(doc, idx))})"
                for idx, picture in enumerate(doc.pictures)
            ]
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

    def convert_document(self, file_content: str, filename: str, include_images: bool):
        request_body = {
            "options": {
                "from_formats": self.config.FROM_FORMATS,
                "to_formats": self.config.TO_FORMATS,
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

        response = httpx.post(
            f"{self.config.API_ENDPOINT}/v1/convert/source",
            json=request_body,
            headers={"Content-Type": "application/json"},
            timeout=self.config.API_TIMEOUT,
        )

        if response.status_code != 200:
            raise ValueError(f"Docling API request failed with status code {response.status_code}: {response.text}")

        return response.json()


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
