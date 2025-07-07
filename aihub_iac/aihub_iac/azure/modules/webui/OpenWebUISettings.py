from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenWebUISettings(BaseSettings):
    OPENWEBUI_OIDC_CLIENT_ID: Annotated[str | None, Field(description="tbd")] = None
    OPENWEBUI_OIDC_CLIENT_SECRET: Annotated[str | None, Field(description="tbd")] = None
    OPENWEBUI_OIDC_PROVIDER_URL: Annotated[str | None, Field(description="tbd")] = None
    OPENWEBUI_OIDC_PROVIDER_NAME: Annotated[str | None, Field(description="tbd")] = None
    OPENWEBUI_AIHUB_API_KEY: Annotated[str | None, Field(description="tbd")] = None
    OPENWEBUI_OPENAI_API_KEY: Annotated[str | None, Field(description="tbd")] = None
    OPENWEBUI_RAG_OPENAI_API_KEY: Annotated[str | None, Field(description="tbd")] = None
    OPENWEBUI_AUDIO_STT_OPENAI_API_KEY: Annotated[str | None, Field(description="tbd")] = None
    OPENWEBUI_AUDIO_TTS_OPENAI_API_KEY: Annotated[str | None, Field(description="tbd")] = None
    OPENWEBUI_IMAGES_OPENAI_API_KEY: Annotated[str | None, Field(description="tbd")] = None
    OPENWEBUI_JINA_API_KEY: Annotated[str | None, Field(description="tbd")] = None
    OPENWEBUI_SECRET_KEY: Annotated[str | None, Field(description="tbd")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
