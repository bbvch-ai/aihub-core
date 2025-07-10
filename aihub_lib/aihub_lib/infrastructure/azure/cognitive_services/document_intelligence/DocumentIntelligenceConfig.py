from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DocumentIntelligenceConfig(BaseSettings):
    DOCUMENTINTELLIGENCE_ENDPOINT: Annotated[
        str | None, Field(pattern=r"^https://.*\.cognitiveservices\.azure\.com/$")
    ] = None
    DOCUMENTINTELLIGENCE_API_KEY: Annotated[str | None, Field(description="API key for Document Intelligence")] = None
    DOCUMENTINTELLIGENCE_API_VERSION: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}(-preview)?$")] = "2024-11-30"
    DOCUMENTINTELLIGENCE_RESOURCE_GROUP_NAME: Annotated[
        str | None, Field(description="Resource Group Name of the Document Intelligence")
    ] = None
    DOCUMENTINTELLIGENCE_NAME: Annotated[
        str | None, Field(description="RName of the Document Intelligence Resource")
    ] = None
    DOCUMENTINTELLIGENCE_EXTENSIONS: Annotated[
        list[str],
        Field(
            description="",
        ),
    ] = [
        "pdf",
        "docx",
        "xlsx",
        "pptx",
        "html",
    ]
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
