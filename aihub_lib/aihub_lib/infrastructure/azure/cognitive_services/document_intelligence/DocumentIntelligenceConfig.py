from typing import Annotated, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DocumentIntelligenceConfig(BaseSettings):
    DOCUMENTINTELLIGENCE_ENDPOINT: Annotated[
        Optional[str], Field(pattern=r"^https://.*\.cognitiveservices\.azure\.com/$")
    ] = None
    DOCUMENTINTELLIGENCE_API_KEY: Annotated[Optional[str], Field(description="API key for Document Intelligence")] = (
        None
    )
    DOCUMENTINTELLIGENCE_API_VERSION: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}(-preview)?$")] = "2024-11-30"
    DOCUMENTINTELLIGENCE_RESOURCE_GROUP_NAME: Annotated[
        Optional[str], Field(description="Resource Group Name of the Document Intelligence")
    ] = None
    DOCUMENTINTELLIGENCE_NAME: Annotated[
        Optional[str], Field(description="RName of the Document Intelligence Resource")
    ] = None
    DOCUMENTINTELLIGENCE_EXTENSIONS: Annotated[
        List[str],
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
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
