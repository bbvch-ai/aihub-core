from typing import Annotated

from pydantic import Field, computed_field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class DefaultTenantSettings(EnvironmentSettings):
    """
    Configuration for default tenant creation.

    These settings control the default tenant that is created on first startup.
    The default tenant provides backwards compatibility with single-tenant deployments.
    """

    model_config = EnvironmentSettings.create_settings_config("AIHUB_DEFAULT_TENANT_")

    ID: Annotated[
        str,
        Field(description="Unique identifier for the default tenant. Also used as the Keycloak group name."),
    ] = "default"

    NAME: Annotated[
        str,
        Field(description="Display name of the default tenant."),
    ] = "Default Organization"

    DESCRIPTION: Annotated[
        str,
        Field(description="Description of the default tenant."),
    ] = "The default organization for all users."

    ACCESS_RULES: Annotated[
        str,
        Field(
            description=(
                "Comma-separated access rules for the default tenant. "
                "Use 'aihub.admin.>' for unrestricted access to all platform features."
            ),
        ),
    ] = "aihub.admin.>"

    @computed_field
    @property
    def access_rules_list(self) -> list[str]:
        """Returns the default tenant access rules as a list."""
        return [r.strip() for r in self.ACCESS_RULES.split(",") if r.strip()]
