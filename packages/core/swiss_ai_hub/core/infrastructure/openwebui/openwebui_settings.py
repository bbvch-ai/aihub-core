from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class OpenWebuiSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("OPENWEBUI_")

    BASE_URL: Annotated[str, Field(description="OpenWebUI server base URL")]
    SECRET_KEY: Annotated[SecretStr, Field(description="OpenWebUI WEBUI_SECRET_KEY for JWT signing")]
    SCIM_TOKEN: Annotated[SecretStr, Field(description="SCIM 2.0 bearer token for group and user provisioning")]
    WEBHOOK_SECRET: Annotated[SecretStr, Field(description="Shared secret for authenticating OpenWebUI webhook calls")]
    SERVICE_ACCOUNT_ID: Annotated[str, Field(description="UUID of the AI-Hub service account in OpenWebUI's database")]
    MODEL_NAME_LOCALE: Annotated[
        str,
        Field(
            description="Locale used to render agent workspace-model names in OpenWebUI, "
            "which only stores a single name per model. Falls back to the platform default "
            "locale and then any available translation."
        ),
    ] = "en"
