from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class OpenWebUISettings(BaseSettings):
    OPENWEBUI_OIDC_CLIENT_ID: Optional[str] = Field(..., description="tbd")
    OPENWEBUI_OIDC_CLIENT_SECRET: Optional[str] = Field(..., description="tbd")
    OPENWEBUI_OIDC_PROVIDER_URL: Optional[str] = Field(..., description="tbd")
    OPENWEBUI_OIDC_PROVIDER_NAME: Optional[str] = Field(..., description="tbd")
    OPENWEBUI_OPENAI_API_KEY: Optional[str] = Field(..., description="tbd")
    OPENWEBUI_RAG_OPENAI_API_KEY: Optional[str] = Field(..., description="tbd")
    OPENWEBUI_AUDIO_STT_OPENAI_API_KEY: Optional[str] = Field(..., description="tbd")
    OPENWEBUI_AUDIO_TTS_OPENAI_API_KEY: Optional[str] = Field(..., description="tbd")
    OPENWEBUI_IMAGES_OPENAI_API_KEY: Optional[str] = Field(..., description="tbd")
    OPENWEBUI_JINA_API_KEY: Optional[str] = Field(..., description="tbd")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
