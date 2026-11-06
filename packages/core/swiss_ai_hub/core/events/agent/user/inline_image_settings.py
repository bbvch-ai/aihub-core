from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class InlineImageSettings(EnvironmentSettings):
    """Bounds on images an API caller sends inside a message to an agent."""

    model_config = EnvironmentSettings.create_settings_config("AGENT_INLINE_IMAGE_")

    MAX_BYTES: Annotated[
        int,
        Field(
            description="Largest image accepted, in bytes. Keep it at or below the gateway's "
            "RAG_IMAGE_INLINE_MAX_BYTES: the gateway hands a larger image to the model as a text marker instead."
        ),
    ] = 5 * 1024 * 1024
