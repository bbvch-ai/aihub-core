from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AzureDocumentIntelligenceSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("AZURE_DOCUMENT_INTELLIGENCE_")

    ENDPOINT: Annotated[str | None, Field(pattern=r"^https://.*\.cognitiveservices\.azure\.com/$")] = None
    API_KEY: Annotated[SecretStr | None, Field(description="API key for Document Intelligence")] = None
    API_VERSION: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}(-preview)?$")] = "2024-11-30"
    RESOURCE_GROUP_NAME: Annotated[
        str | None, Field(description="Resource Group Name of the Document Intelligence")
    ] = None
    RESOURCE_NAME: Annotated[str | None, Field(description="Name of the Document Intelligence Resource")] = None
    EXTENSIONS: Annotated[
        list[str],
        Field(
            description="",
        ),
    ] = [
        "jpg",
        "jpeg",
        "png",
        "bmp",
        "tiff",
        "pdf",
        "heif",
        "docx",
        "xlsx",
        "pptx",
        "html",
    ]
