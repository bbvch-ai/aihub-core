from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Config(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )