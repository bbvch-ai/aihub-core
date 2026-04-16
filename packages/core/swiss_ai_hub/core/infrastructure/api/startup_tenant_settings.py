from typing import Annotated

from pydantic import Field, computed_field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class StartupTenantSettings(EnvironmentSettings):
    """
    Configuration for the tenant the platform seeds on first startup.

    Once created, it is an ordinary tenant — no special flags in the database,
    no special treatment in authorization. The only thing "startup" about it is
    that the first-boot initialization reads its id/name/etc. from these
    settings instead of from a sysadmin's create-tenant request.
    """

    model_config = EnvironmentSettings.create_settings_config("AIHUB_STARTUP_TENANT_")

    ID: Annotated[
        str,
        Field(description="Unique identifier for the startup tenant. Also used as the Keycloak group name."),
    ] = "default"

    NAME: Annotated[
        str,
        Field(description="Display name of the startup tenant."),
    ] = "Swiss AI Hub"

    DESCRIPTION: Annotated[
        str,
        Field(description="Description of the startup tenant."),
    ] = "This tenant was auto-created on startup of the Swiss AI Hub.."

    ACCESS_RULES: Annotated[
        str,
        Field(
            description=(
                "Comma-separated access rules for the startup tenant. "
                "Use 'aihub.admin.>' for unrestricted access to all platform features."
            ),
        ),
    ] = "aihub.admin.>"

    @computed_field
    @property
    def access_rules_list(self) -> list[str]:
        """Returns the startup tenant access rules as a list."""
        return [r.strip() for r in self.ACCESS_RULES.split(",") if r.strip()]
