from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DocumentIntelligenceConfig(BaseSettings):
    DOCUMENTINTELLIGENCE_ENDPOINT: Optional[str] = Field(None, pattern=r"^https://.*\.cognitiveservices\.azure\.com/$")
    DOCUMENTINTELLIGENCE_API_KEY: Optional[str] = Field(None, description="API key for Document Intelligence")
    DOCUMENTINTELLIGENCE_API_VERSION: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}(-preview)?$")
    DOCUMENTINTELLIGENCE_RESOURCE_GROUP_NAME: Optional[str] = Field(
        None, description="Resource Group Name of the Document Intelligence"
    )
    DOCUMENTINTELLIGENCE_NAME: Optional[str] = Field(None, description="RName of the Document Intelligence Resource")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
