from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Config(BaseSettings):
    ENDPOINT_URL: str = "http://localhost:9000"
    ACCESS_KEY: str = "minioadmin"
    SECRET_KEY: str = "minioadmin"
    REGION: str = "us-east-1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="S3_",
    )
