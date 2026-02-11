from typing import Annotated

from langfuse import Langfuse
from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class LangfuseSettings(EnvironmentSettings):
    """Configuration for Langfuse observability platform."""

    model_config = EnvironmentSettings.create_settings_config("LANGFUSE_")

    BASEURL: Annotated[str, Field(pattern=r"^https?://.*$", description="Langfuse server base URL")]
    PUBLIC_KEY: Annotated[str, Field(description="Langfuse public API key")]
    SECRET_KEY: Annotated[SecretStr, Field(description="Langfuse secret API key")]
    TIMEOUT: Annotated[int, Field(description="Timeout in seconds for Langfuse API requests")] = 60
    PUBLIC_URL: Annotated[
        str | None,
        Field(description="Public-facing Langfuse URL for browser links (e.g. https://langfuse.example.com)"),
    ] = None
    PROJECT_ID: Annotated[
        str | None,
        Field(description="Langfuse project ID for constructing dataset URLs"),
    ] = None

    def create_client(self) -> Langfuse:
        """Create a Langfuse client with SDK tracing disabled since we use OTEL instead."""
        return Langfuse(
            public_key=self.PUBLIC_KEY,
            secret_key=self.SECRET_KEY.get_secret_value(),
            host=self.BASEURL,
            timeout=self.TIMEOUT,
            tracing_enabled=False,
        )
