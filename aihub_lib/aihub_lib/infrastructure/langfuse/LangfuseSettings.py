from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class LangfuseSettings(EnvironmentSettings):
    """
    Configuration settings for Langfuse observability and evaluation platform.

    Langfuse provides LLM observability, evaluation, and experiment management
    with an MIT-licensed open-source self-hosted option.
    """

    model_config = EnvironmentSettings.create_settings_config("LANGFUSE_")

    BASEURL: Annotated[str, Field(pattern=r"^https?://.*$", description="Langfuse server base URL")]
    PUBLIC_KEY: Annotated[str, Field(description="Langfuse public API key")]
    SECRET_KEY: Annotated[SecretStr, Field(description="Langfuse secret API key")]
