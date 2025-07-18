from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DoclingConfig(BaseSettings):
    DOCLING_API_ENDPOINT: Annotated[
        str, Field("http://localhost:5001/v1alpha/convert/source", description="Docling API endpoint URL")
    ]
    DOCLING_API_TIMEOUT: Annotated[int, Field(300, description="Timeout for Docling API calls in seconds")]
    DOCLING_FROM_FORMATS: Annotated[
        list[str],
        Field(
            description="Input formats for Docling",
        ),
    ] = [
        "docx",
        "pptx",
        "html",
        "image",
        "pdf",
        "asciidoc",
        "csv",
        "xlsx",
        "xml_uspto",
        "xml_jats",
        "json_docling",
        "audio",
    ]
    DOCLING_TO_FORMATS: Annotated[list[str], Field(description="Output formats")] = ["md", "json"]
    DOCLING_IMAGE_EXPORT_MODE: Annotated[
        str,
        Field(description="Images should be embedded in Markdown or referenced or placeholder is used"),
    ] = "embedded"
    DOCLING_DO_OCR: Annotated[bool, Field(description="Whether to perform OCR")] = True
    DOCLING_FORCE_OCR: Annotated[bool, Field(description="Whether to force OCR")] = True
    DOCLING_OCR_ENGINE: Annotated[str, Field(default="easyocr", description="OCR engine to use")]
    DOCLING_PDF_BACKEND: Annotated[str, Field(default="dlparse_v4", description="PDF parsing backend")]
    DOCLING_TABLE_MODE: Annotated[
        str, Field(default="accurate", description="Table extraction mode, options: 'accurate', 'fast'")
    ]
    DOCLING_IMAGES_SCALE: Annotated[
        int, Field(default=2, description="Scale factor for images, when embedded in Markdown")
    ]
    MD_PAGE_BREAK_PLACEHOLDER: Annotated[
        str, Field(default="<!-- PageBreak -->", description="Placeholder for page breaks in Markdown output")
    ]
    DOCLING_EXTENSIONS: Annotated[
        list[str],
        Field(
            description="",
        ),
    ] = [
        "docx",
        "dotx",
        "docm",
        "dotm",
        "pptx",
        "potx",
        "ppsx",
        "pptm",
        "potm",
        "ppsm",
        "pdf",
        "html",
        "htm",
        "xhtml",
        "xml",
        "nxml",
        "jpg",
        "jpeg",
        "png",
        "tif",
        "tiff",
        "bmp",
        "webp",
        "adoc",
        "asciidoc",
        "asc",
        "csv",
        "xlsx",
        "xlsm",
        "xml",
        "txt",
        "json",
        "wav",
        "mp3",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
