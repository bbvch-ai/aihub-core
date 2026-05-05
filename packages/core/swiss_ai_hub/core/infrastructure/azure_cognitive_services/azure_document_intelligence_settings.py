from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class AzureDocumentIntelligenceSettings(EnvironmentSettings):
    """
    Configuration for Azure Document Intelligence (formerly Form Recognizer).

    Authentication uses explicit API key (token-based authentication).
    Both ENDPOINT and API_KEY are required.
    """

    model_config = EnvironmentSettings.create_settings_config("AZURE_DOCUMENT_INTELLIGENCE_")

    ENDPOINT: Annotated[str, Field(pattern=r"^https://.*\.cognitiveservices\.azure\.com/$")]
    API_KEY: Annotated[SecretStr, Field(description="API key for Document Intelligence")]
    API_VERSION: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}(-preview)?$")]
    EXTENSIONS: Annotated[
        list[str],
        Field(
            description="Supported file extensions for document processing",
        ),
    ] = [
        "pdf",
        "docx",
        "xlsx",
        "pptx",
        "html",
    ]
