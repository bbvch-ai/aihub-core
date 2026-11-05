from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class InlineFileSettings(EnvironmentSettings):
    """Bounds on files an API caller sends inside the request instead of uploading them first."""

    model_config = EnvironmentSettings.create_settings_config("AGENT_INLINE_FILE_")

    MAX_FILE_BYTES: Annotated[int, Field(description="Largest decoded file accepted, in bytes.")] = 25 * 1024 * 1024
    MAX_FILES_PER_REQUEST: Annotated[int, Field(description="How many inline files one request may carry.")] = 10
