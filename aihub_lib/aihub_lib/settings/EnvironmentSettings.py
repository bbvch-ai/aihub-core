from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentSettings(BaseSettings):
    @staticmethod
    def create_settings_config(prefix: str) -> SettingsConfigDict:
        env_file = Path(__file__).parent.parent.parent.parent / ".env"
        if not env_file.exists():
            env_file = None

        return SettingsConfigDict(
            env_file=env_file,
            env_file_encoding="utf-8",
            extra="ignore",
            env_prefix=prefix,
            arbitrary_types_allowed=True,
        )
