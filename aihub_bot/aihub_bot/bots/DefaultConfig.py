from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

""" Bot Configuration """


class DefaultConfig(BaseSettings):
    """Bot Configuration"""

    APP_ID: Annotated[str, Field(..., description="Microsoft App ID")]
    APP_PASSWORD: Annotated[str, Field(..., description="Microsoft App Password")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
