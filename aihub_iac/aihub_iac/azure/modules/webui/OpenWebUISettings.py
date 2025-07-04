from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenWebUISettings(BaseSettings):
    OPENWEBUI_OIDC_CLIENT_ID: Annotated[Optional[str], Field(description="tbd")] = None
    OPENWEBUI_OIDC_CLIENT_SECRET: Annotated[Optional[str], Field(description="tbd")] = None
    OPENWEBUI_OIDC_PROVIDER_URL: Annotated[Optional[str], Field(description="tbd")] = None
    OPENWEBUI_OIDC_PROVIDER_NAME: Annotated[Optional[str], Field(description="tbd")] = None
    OPENWEBUI_AIHUB_API_KEY: Annotated[Optional[str], Field(description="tbd")] = None
    OPENWEBUI_OPENAI_API_KEY: Annotated[Optional[str], Field(description="tbd")] = None
    OPENWEBUI_RAG_OPENAI_API_KEY: Annotated[Optional[str], Field(description="tbd")] = None
    OPENWEBUI_AUDIO_STT_OPENAI_API_KEY: Annotated[Optional[str], Field(description="tbd")] = None
    OPENWEBUI_AUDIO_TTS_OPENAI_API_KEY: Annotated[Optional[str], Field(description="tbd")] = None
    OPENWEBUI_IMAGES_OPENAI_API_KEY: Annotated[Optional[str], Field(description="tbd")] = None
    OPENWEBUI_JINA_API_KEY: Annotated[Optional[str], Field(description="tbd")] = None
    OPENWEBUI_SECRET_KEY: Annotated[Optional[str], Field(description="tbd")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
