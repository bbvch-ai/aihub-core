from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LiteLLMProxyConfig(BaseSettings):
    LITE_LLM_PROXY_BASE_URL: Annotated[str, Field(description="The base URL of the model.")]
    LITE_LLM_PROXY_API_KEY: Annotated[
        str | None,
        Field(description="API key for authentication. If not provided, other authentication methods will be used."),
    ] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )