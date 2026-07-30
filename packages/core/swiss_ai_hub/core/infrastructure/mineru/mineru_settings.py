from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


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

    VLM_SERVER_URL: Annotated[str, Field(description="LiteLLM proxy URL for VLM routing")] = "http://litellm:4000"
    VLM_SERVER_API_KEY: Annotated[SecretStr, Field(description="LiteLLM API key for VLM requests")] = SecretStr("")
    VLM_NAME: Annotated[str, Field(description="LiteLLM model alias for MinerU VLM")] = (
        "text-generation/MinerU2.5-2509-1.2B"
    )

    FORMULA_ENABLE: Annotated[bool, Field(description="Enable formula/equation parsing")] = True
    TABLE_ENABLE: Annotated[bool, Field(description="Enable table detection and parsing")] = True

    PAGE_BATCH_SIZE: Annotated[
        int,
        Field(description="Pages per MinerU request for PDFs; keeps server memory constant. 0 disables batching"),
    ] = 25
    MAX_CONCURRENT_BATCH_REQUESTS: Annotated[
        int,
        Field(description="Client-side concurrent page-batch requests per document"),
    ] = 2

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
