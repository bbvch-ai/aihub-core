from typing import Annotated

from pydantic import Field, computed_field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class TenantSettings(EnvironmentSettings):
    """
    Configuration for the multi-tenant system.

    These settings control:
    - Default tenant creation on first startup
    - Default roles assigned to new users
    - First user (admin) role assignment
    """

    model_config = EnvironmentSettings.create_settings_config("TENANT_")

    DEFAULT_NAME: Annotated[
        str,
        Field(description="Name of the default tenant created on first startup."),
    ] = "Default Organization"

    DEFAULT_DESCRIPTION: Annotated[
        str,
        Field(description="Description of the default tenant."),
    ] = "The default organization for all users."

    DEFAULT_ACCESS_RULES: Annotated[
        str,
        Field(
            description=("Comma-separated access rules for the default tenant. Use 'aihub.>' for unrestricted access."),
        ),
    ] = "aihub.>"

    USER_SIGNUP_DEFAULT_ROLES: Annotated[
        str,
        Field(
            description=("Comma-separated list of roles assigned to new users when they sign up."),
        ),
    ] = "AIHubUser"

    FIRST_USER_SIGNUP_DEFAULT_ROLES: Annotated[
        str,
        Field(
            description=(
                "Comma-separated list of roles assigned to the very first user. "
                "This user is typically the initial admin."
            ),
        ),
    ] = "AIHubAdmin,AIHubUser"

    @computed_field
    @property
    def default_access_rules_list(self) -> list[str]:
        """Returns the default tenant access rules as a list."""
        return [r.strip() for r in self.DEFAULT_ACCESS_RULES.split(",") if r.strip()]

    @computed_field
    @property
    def user_signup_default_roles_list(self) -> list[str]:
        """Returns the default user signup roles as a list."""
        return [r.strip() for r in self.USER_SIGNUP_DEFAULT_ROLES.split(",") if r.strip()]

    @computed_field
    @property
    def first_user_signup_default_roles_list(self) -> list[str]:
        """Returns the first user signup roles as a list."""
        return [r.strip() for r in self.FIRST_USER_SIGNUP_DEFAULT_ROLES.split(",") if r.strip()]
