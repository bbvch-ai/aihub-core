from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class AuthSettings(EnvironmentSettings):
    """
    Authentication settings for the API.

    All OAuth2/OIDC authentication goes through Keycloak, which acts as an
    identity broker for upstream providers (Azure AD, Google, etc.).
    """

    model_config = EnvironmentSettings.create_settings_config("AUTH_")

    ENABLE_API_ACCESS: Annotated[bool, Field(description="Enable API access")] = True
    OPEN_WEBUI_SIGNING_SECRET: Annotated[SecretStr, Field(description="OpenWebUI signing secret", min_length=64)]
