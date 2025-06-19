from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DoclingConfig(BaseSettings):
    DOCLING_API_ENDPOINT: str = Field(
        "http://localhost:5001/v1alpha/convert/source", description="Docling API endpoint URL"
    )
    DOCLING_API_TIMEOUT: int = Field(300, description="Timeout for Docling API calls in seconds")
    DOCLING_FROM_FORMATS: List[str] = Field(
        [
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
        description="Supported input formats",
    )
    DOCLING_TO_FORMATS: List[str] = Field(["md", "json"], description="Output formats")
    DOCLING_IMAGE_EXPORT_MODE: str = Field("embedded", description="Image export mode")
    DOCLING_DO_OCR: bool = Field(True, description="Whether to perform OCR")
    DOCLING_FORCE_OCR: bool = Field(True, description="Whether to force OCR")
    DOCLING_OCR_ENGINE: str = Field("easyocr", description="OCR engine to use")
    DOCLING_PDF_BACKEND: str = Field("dlparse_v4", description="PDF parsing backend")
    DOCLING_TABLE_MODE: str = Field("accurate", description="Table extraction mode")
    DOCLING_IMAGES_SCALE: int = Field(2, description="Scale factor for images")
    MD_PAGE_BREAK_PLACEHOLDER: str = Field(
        "<!-- PageBreak -->", description="Placeholder for page breaks in Markdown output"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
