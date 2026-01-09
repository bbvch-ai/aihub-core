from enum import Enum
from typing import Annotated

from pydantic import Field

from aihub_lib.generative_ai.document.loaders.DocumentIntelligenceLoader import PAGE_BREAK
from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class PipelineType(Enum):
    """Enum for document loader types."""

    VLM = "vlm"
    STANDARD = "standard"


class DoclingSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("DOCLING_")

    # --- General API Settings ---
    BASE_API_URL: Annotated[str, Field(description="Docling API endpoint URL")]
    API_TIMEOUT: Annotated[int, Field(description="Timeout for individual Docling API calls in seconds")] = 300
    OPERATION_TIMEOUT: Annotated[
        int, Field(description="Overall timeout for entire aload_data operation in seconds")
    ] = 3600  # 1 hour

    # --- Pipeline Type ---
    PIPELINE_TYPE: Annotated[PipelineType, Field(description="The type of pipeline to use")] = PipelineType.STANDARD

    # --- VLM Pipeline Settings (Permanent) ---
    HOSTED_VLM_API_ENDPOINT: Annotated[str, Field(description="The API endpoint for the self-hosted VLM")] = (
        "http://litellm:4000"
    )
    HOSTED_VLM_API_KEY: Annotated[str, Field(description="The API key for the self-hosted VLM")] = ""
    VLM_MODEL_NAME: Annotated[str, Field(description="The model name for the VLM")] = "text-generation/ocr"

    # --- Output Format ---
    TO_FORMATS: Annotated[list[str], Field(description="Output formats")] = ["json"]

    # --- Application-Specific Settings ---
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
        PAGE_BREAK
    )
    EXTENSIONS: Annotated[
        list[str],
        Field(
            description="File extensions supported by the application.",
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
        "json",
        "wav",
        "mp3",
    ]

    # --- Async Polling Settings ---
    POLL_INTERVAL: Annotated[int, Field(description="Interval between polling attempts in seconds")] = 4
    MAX_POLLS: Annotated[int, Field(description="Maximum number of polling attempts")] = 300

    # --- Retry Settings ---
    HTTP_RETRIES: Annotated[int, Field(description="Number of retries for transient HTTP errors")] = 3

    # --- Cleanup Settings ---
    CLEAR_RESULTS_DELAY: Annotated[int, Field(description="Delay in seconds for clearing old results after fetch")] = 30
