from enum import Enum
from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class PipelineType(Enum):
    """Enum for document loader types."""

    VLM = "vlm"
    STANDARD = "standard"


class DoclingSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("DOCLING_")

    # --- General API Settings ---
    BASE_API_URL: Annotated[str, Field(description="Docling API endpoint URL")]
    API_TIMEOUT: Annotated[int, Field(description="Timeout for Docling API calls in seconds")] = 300

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
