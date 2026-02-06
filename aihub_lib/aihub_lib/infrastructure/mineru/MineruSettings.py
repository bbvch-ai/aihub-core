from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class MineruSettings(EnvironmentSettings):
    """
    Configuration settings for MinerU document parsing service.

    MinerU is used as the primary document parser for PDFs and images,
    providing high-quality OCR and document structure extraction.

    The VLM (Vision Language Model) is accessed through LiteLLM for
    unified model routing and fallback support.
    """

    model_config = EnvironmentSettings.create_settings_config("MINERU_")

    API_BASE_URL: Annotated[str, Field(description="MinerU API endpoint URL")] = "http://mineru-api:8000"
    API_TIMEOUT: Annotated[int, Field(description="Timeout for MinerU API calls in seconds")] = 600

    VL_SERVER_URL: Annotated[str, Field(description="LiteLLM proxy URL for VLM routing")] = "http://litellm:4000"
    VL_API_KEY: Annotated[SecretStr, Field(description="LiteLLM API key for VLM requests")] = SecretStr("")
    VL_MODEL_NAME: Annotated[str, Field(description="LiteLLM model alias for MinerU VLM")] = "text-generation/ocr"

    FORMULA_ENABLE: Annotated[bool, Field(description="Enable formula/equation parsing")] = True
    TABLE_ENABLE: Annotated[bool, Field(description="Enable table detection and parsing")] = True

    EXTENSIONS: Annotated[
        list[str],
        Field(description="File extensions supported by MinerU"),
    ] = [
        "pdf",
        "png",
        "jpeg",
        "jp2",
        "webp",
        "gif",
        "bmp",
        "jpg",
        "tiff",
    ]
