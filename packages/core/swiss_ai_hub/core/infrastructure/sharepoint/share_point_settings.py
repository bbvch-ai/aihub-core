from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class SharePointSettings(EnvironmentSettings):
    """
    Configuration settings for SharePoint integration.

    This configuration class manages connection parameters and filtering options
    for SharePoint document synchronization. It uses Pydantic BaseSettings
    to load configuration from environment variables with fallback defaults.
    """

    model_config = EnvironmentSettings.create_settings_config("SHAREPOINT_")

    TENANT_ID: Annotated[str, Field(description="The Azure AD tenant ID.")]
    CLIENT_ID: Annotated[str, Field(description="The application (client) ID.")]
    CLIENT_SECRET: Annotated[SecretStr, Field(description="The client secret for authentication.")]
    SITE_URL: Annotated[str, Field(description="The SharePoint site URL.")]
