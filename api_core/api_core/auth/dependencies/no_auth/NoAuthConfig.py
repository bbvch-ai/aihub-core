import uuid
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NoAuthConfig(BaseSettings):
    NAME: str = Field(..., description="User name")
    EMAIL: str = Field(..., description="User email")
    OID: str = Field(..., description="User OID", default_factory=lambda: str(uuid.uuid4()))
    ROLES: List[str] = Field(..., description="User roles")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )