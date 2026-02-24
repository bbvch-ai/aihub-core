from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AuthSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("AUTH_")

    ENABLE_API_ACCESS: Annotated[bool, Field(description="Enable API access")] = True
    OPEN_WEBUI_SIGNING_SECRET: Annotated[SecretStr, Field(description="OpenWebUI signing secret", min_length=64)]
