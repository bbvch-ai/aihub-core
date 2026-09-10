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

    CONVERSATION_METADATA_MODEL: Annotated[
        str,
        Field(
            description="LiteLLM name (``capability/name``) of the model generating conversation metadata — chat "
            "titles and follow-up questions — for chats that have no agent behind them. OpenWebUI runs it under "
            "the end user's identity, so a role without access to this model loses both features silently; the "
            "access catalog flags the model for that reason. Same model as the OpenWebUI ``TASK_MODEL`` env var "
            "but in LiteLLM form, since that one names the workspace model wrapping it."
        ),
    ] = "text-generation/gemma-4-31B-it"

    @field_validator("MODEL_NAME_LOCALE", mode="before")
    @classmethod
    def _default_blank_locale(cls, value: str | None) -> str:
        """An unset compose-interpolated ``${OPENWEBUI_MODEL_NAME_LOCALE}`` arrives as an empty string that
        bypasses the field default, so coerce blank values back to ``en`` rather than letting LocaleHandler
        fall back to its own default."""

        locale = (value or "").strip()
        if not locale:
            return "en"
        if locale not in LocaleHandler.LOCALE_WHITE_LIST:
            raise ValueError(
                f"OPENWEBUI_MODEL_NAME_LOCALE must be one of {LocaleHandler.LOCALE_WHITE_LIST}, got {locale!r}"
            )
        return locale
