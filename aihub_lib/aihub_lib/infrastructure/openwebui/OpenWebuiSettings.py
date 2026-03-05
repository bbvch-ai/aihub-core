from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class OpenWebuiSettings(EnvironmentSettings):
    """Configuration for OpenWebUI server connection."""

    model_config = EnvironmentSettings.create_settings_config("OPENWEBUI_")

    BASE_URL: Annotated[str, Field(description="OpenWebUI server base URL")]
    API_KEY: Annotated[SecretStr, Field(description="OpenWebUI admin API key")]
