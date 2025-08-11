from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AuthSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("AUTH_")

    ENABLE_API_ACCESS: Annotated[bool, Field(description="Enable API access")] = True
    OPEN_WEBUI_SIGNING_SECRET: Annotated[str, Field(description="OpenWebUI signing secret")]
    IDENTITY_PROVIDER: Annotated[Literal["azure"], Field(description="OAuth provider")] = "azure"
