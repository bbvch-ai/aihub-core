from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentSettings(BaseSettings):
    @staticmethod
    def create_settings_config(
        prefix: str,
        extra: Literal["allow", "ignore", "forbid"] = "ignore",
    ) -> SettingsConfigDict:
        env_file = Path(__file__).parent.parent.parent.parent / ".env"
        if not env_file.exists():
            env_file = None

        return SettingsConfigDict(
            env_file=env_file,
            env_file_encoding="utf-8",
            extra=extra,
            env_prefix=prefix,
            arbitrary_types_allowed=True,
        )
