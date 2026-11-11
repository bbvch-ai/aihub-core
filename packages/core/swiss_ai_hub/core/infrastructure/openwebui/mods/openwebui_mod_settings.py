from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class OpenWebuiModSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("OPENWEBUI_MODS_")

    DEFAULTS: Annotated[
        list[str],
        Field(max_length=64, description="JSON array of bundled mod IDs enabled until a tenant saves its own configuration."),
    ] = Field(default_factory=list)
