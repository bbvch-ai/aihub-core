from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class LangfuseBootstrapSettings(EnvironmentSettings):
    """Settings for registering AI-Hub LLM connections and evaluator scaffolding in Langfuse on startup."""

    model_config = EnvironmentSettings.create_settings_config("LANGFUSE_BOOTSTRAP_")

    AIHUB_CONNECTION_NAME: Annotated[str, Field(description="Display name for AI-Hub connection in Langfuse UI")] = (
        "AI-Hub Agents"
    )

    AIHUB_BASE_URL: Annotated[
        str,
        Field(
            pattern=r"^https?://.*$",
            description="Base URL for AI-Hub's OpenAI-compatible endpoint (internal Docker URL)",
        ),
    ] = "http://aihub-api:8000/api/v1/openai"

    AIHUB_API_KEY: Annotated[
        SecretStr | None,
        Field(description="API key for Langfuse to authenticate with AI-Hub. If None, uses internal networking."),
    ] = None

    LITELLM_CONNECTION_NAME: Annotated[
        str, Field(description="Display name for LiteLLM evaluator connection in Langfuse UI")
    ] = "AI-Hub LLM (Evaluators)"

    LITELLM_BASE_URL: Annotated[
        str,
        Field(
            pattern=r"^https?://.*$",
            description="Base URL for LiteLLM proxy",
        ),
    ] = "http://litellm:4000"

    LITELLM_API_KEY: Annotated[
        SecretStr | None,
        Field(description="API key for LiteLLM proxy. If None, LiteLLM connection won't be registered."),
    ] = None

    ENABLED: Annotated[bool, Field(description="Whether to run bootstrap on startup")] = True
