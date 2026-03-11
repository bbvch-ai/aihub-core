from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class OpenWebuiSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("OPENWEBUI_")

    BASE_URL: Annotated[str, Field(description="OpenWebUI server base URL")]
    SECRET_KEY: Annotated[SecretStr, Field(description="OpenWebUI WEBUI_SECRET_KEY for JWT signing")]
    SCIM_TOKEN: Annotated[SecretStr, Field(description="SCIM 2.0 bearer token for group and user provisioning")]
    WEBHOOK_SECRET: Annotated[SecretStr, Field(description="Shared secret for authenticating OpenWebUI webhook calls")]
    SERVICE_ACCOUNT_ID: Annotated[str, Field(description="UUID of the AI-Hub service account in OpenWebUI's database")]
