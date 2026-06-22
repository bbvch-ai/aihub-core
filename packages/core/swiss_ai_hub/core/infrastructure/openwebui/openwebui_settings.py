from typing import Annotated

from pydantic import Field, SecretStr, field_validator

from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
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

    @field_validator("MODEL_NAME_LOCALE", mode="before")
    @classmethod
    def _default_blank_locale(cls, value: str | None) -> str:
        """A compose-interpolated unset ``${OPENWEBUI_MODEL_NAME_LOCALE}`` arrives as an empty string that bypasses the
        field default, so coerce blank values back to en rather than letting LocaleHandler fall back to its own default."""

        locale = (value or "").strip()
        if not locale:
            return "en"
        if locale not in LocaleHandler.LOCALE_WHITE_LIST:
            raise ValueError(
                f"OPENWEBUI_MODEL_NAME_LOCALE must be one of {LocaleHandler.LOCALE_WHITE_LIST}, got {locale!r}"
            )
        return locale
