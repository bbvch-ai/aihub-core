from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class OpenWebuiSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("OPENWEBUI_")

    BASE_URL: Annotated[str, Field(description="OpenWebUI server base URL")]
    SECRET_KEY: Annotated[SecretStr, Field(description="OpenWebUI WEBUI_SECRET_KEY for JWT signing")]
    SERVICE_ACCOUNT_ID: Annotated[str, Field(description="UUID of the AI-Hub service account in OpenWebUI's database")]
