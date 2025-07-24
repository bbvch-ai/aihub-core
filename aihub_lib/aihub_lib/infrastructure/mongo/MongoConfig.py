from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoConfig(BaseSettings):
    MONGO_CONNECTION_STRING: Annotated[str | None, Field(description="Overwrite the MongoDB connection string")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
