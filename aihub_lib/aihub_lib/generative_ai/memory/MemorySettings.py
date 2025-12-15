from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class MemorySettings(EnvironmentSettings):
    """Settings for memory management system."""

    model_config = EnvironmentSettings.create_settings_config("MEMORY_")

    DEFAULT_TENANT_ID: Annotated[str, Field(description="Default tenant ID for memory scoping")] = "AIHub"

    DEFAULT_TENANT_NAMESPACE: Annotated[
        str | None, Field(description="Default tenant namespace for department-level scoping")
    ] = "Engineering"
