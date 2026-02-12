from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Docker secrets directory - standard location for Docker Swarm/Compose secrets
DOCKER_SECRETS_DIR = Path("/run/secrets")


class EnvironmentSettings(BaseSettings):
    """
    Base settings class that supports both environment variables and Docker secrets.

    Docker secrets take lower priority than environment variables, allowing env vars
    to override secrets when needed (e.g., for local development). Secret files should
    be named with the full prefixed variable name in lowercase (e.g., 'nats_token').
    """

    @staticmethod
    def create_settings_config(
        prefix: str,
        extra: Literal["allow", "ignore", "forbid"] = "ignore",
    ) -> SettingsConfigDict:
        env_file = Path(__file__).parent.parent.parent.parent / ".env"
        if not env_file.exists():
            env_file = None

        # Only use secrets_dir if the directory exists (i.e., running in Docker with secrets)
        secrets_dir = DOCKER_SECRETS_DIR if DOCKER_SECRETS_DIR.exists() else None

        return SettingsConfigDict(
            env_file=env_file,
            env_file_encoding="utf-8",
            extra=extra,
            env_prefix=prefix,
            arbitrary_types_allowed=True,
            secrets_dir=secrets_dir,
        )
