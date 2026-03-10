from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.EnvironmentSettings import EnvironmentSettings


class MemorySettings(EnvironmentSettings):
    """Settings for memory management system."""

    model_config = EnvironmentSettings.create_settings_config("MEMORY_")

    DEFAULT_TENANT_ID: Annotated[str, Field(description="Default tenant ID for memory scoping")] = "AIHub"

    DEFAULT_TENANT_NAMESPACE: Annotated[
        str | None, Field(description="Default tenant namespace for department-level scoping")
    ] = None
