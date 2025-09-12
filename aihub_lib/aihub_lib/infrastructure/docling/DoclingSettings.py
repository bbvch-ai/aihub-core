from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class DoclingSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("DOCLING_")

    API_ENDPOINT: Annotated[str, Field(description="Docling API endpoint URL")]
    API_TIMEOUT: Annotated[int, Field(description="Timeout for Docling API calls in seconds")] = 300
    FROM_FORMATS: Annotated[list[str], Field(description="Input formats for Docling")] = [
        "docx",
        "pptx",
        "html",
        "pdf",
        "asciidoc",
        "csv",
        "xlsx",
        "xml_uspto",
        "xml_jats",
        "json_docling",
        "audio",
    ]
    TO_FORMATS: Annotated[list[str], Field(description="Output formats")] = ["json"]
    IMAGE_EXPORT_MODE: Annotated[
        str,
        Field(description="Images should be embedded in Markdown or referenced or placeholder is used"),
    ] = "embedded"
    DO_OCR: Annotated[bool, Field(description="Whether to perform OCR")] = True
    FORCE_OCR: Annotated[bool, Field(description="Whether to force OCR")] = False
    OCR_ENGINE: Annotated[str, Field(description="OCR engine to use")] = "easyocr"
    PDF_BACKEND: Annotated[str, Field(description="PDF parsing backend")] = "dlparse_v4"
    TABLE_MODE: Annotated[str, Field(description="Table extraction mode, options: 'accurate', 'fast'")] = "accurate"
    IMAGES_SCALE: Annotated[int, Field(description="Scale factor for images, when embedded in Markdown")] = 2
    MD_PAGE_BREAK_PLACEHOLDER: Annotated[str, Field(description="Placeholder for page breaks in Markdown output")] = (
        "<!-- PageBreak -->"
    )
    EXTENSIONS: Annotated[
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
    POLL_INTERVAL: Annotated[int, Field(description="Interval between polling attempts in seconds")] = 4
    MAX_POLLS: Annotated[int, Field(description="Maximum number of polling attempts")] = 300
