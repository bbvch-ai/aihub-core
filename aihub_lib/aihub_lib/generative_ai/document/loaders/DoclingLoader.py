import base64
import html
import os
import re
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from fsspec import AbstractFileSystem
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.file.base import get_default_fs
from llama_index.core.schema import Document

from aihub_lib.generative_ai.utils.path_utils import create_data_lake_figures_folder_name
from aihub_lib.persistence.rag.vectors.node_metadata import (
    NODE_CONTENT_TYPE_FIGURE,
    NODE_CONTENT_TYPE_TABLE,
    NUMBER_OF_PAGES,
)

PAGE_BREAK = "<!-- PageBreak -->"


class DoclingLoader(BaseReader):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def load_data(
        self,
        file: str,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
        figures_directory_name: Optional[str] = None,
    ) -> List[Document]:
        fs = fs or get_default_fs()
        with fs.open(file, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read()).decode("utf-8")
        file_name = os.path.basename(file)

        request_body = {
            "options": {
                "from_formats": [
                    "docx",
                    "pptx",
                    "html",
                    "image",
                    "pdf",
                    "asciidoc",
                    "md",
                    "csv",
                    "xlsx",
                    "xml_uspto",
                    "xml_jats",
                    "json_docling",
                ],
                "to_formats": ["md", "json"],
                "image_export_mode": "embedded",
                "do_ocr": True,
                "force_ocr": True,
                "ocr_engine": "easyocr",
                "pdf_backend": "dlparse_v4",
                "table_mode": "accurate",
                "abort_on_error": False,
                "return_as_file": False,
                "do_table_structure": True,
                "include_images": True,
                "images_scale": 2,
                "do_code_enrichment": True,
                "do_formula_enrichment": True,
                "do_picture_classification": False,
                "do_picture_description": False,
                "md_page_break_placeholder": PAGE_BREAK,
            },
            "file_sources": [{"base64_string": encoded_string, "filename": file_name}],
        }

        r = requests.post(
            "http://localhost:5001/v1alpha/convert/source",
            json=request_body,
            headers={"Content-Type": "application/json"},
            timeout=300,
        )
        if r.status_code != 200:
            raise ValueError(f"Docling API request failed with status code {r.status_code}: {r.text}")
        answer = r.json()
        markdown_content = answer["document"]["md_content"]
        markdown_content = extract_base64_images_from_tables(extract_base64_images(markdown_content))

        metadata = {NUMBER_OF_PAGES: len(answer["document"]["json_content"]["pages"])}

        soup = BeautifulSoup(markdown_content, "html.parser")
        figure_tags = soup.find_all("figure")

        figures_dir = create_data_lake_figures_folder_name(file, figures_directory_name)
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


def extract_base64_images(markdown_text):
    """
    Extract base64 encoded images from Markdown text.
    """
    pattern = r"(!\[.*?\]\(data:image/[^;]+;base64,[^\)]+\))"
    markdown_text = re.sub(pattern, f"<{NODE_CONTENT_TYPE_FIGURE}>\\1</{NODE_CONTENT_TYPE_FIGURE}>", markdown_text)

    return markdown_text


# Do the same for tables
def extract_base64_images_from_tables(markdown_text):
    """
    Extract base64 encoded images from Markdown tables.
    """
    pattern = r"(\|[^\n]+\|\r?\n\|[:\-| ]+\|\r?(?:\n\|[^\n]+\|\r?)*)"
    markdown_text = re.sub(pattern, f"<{NODE_CONTENT_TYPE_TABLE}>\\1</{NODE_CONTENT_TYPE_TABLE}>", markdown_text)

    return markdown_text
