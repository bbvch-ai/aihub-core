from typing import Annotated

from pydantic import Field, computed_field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class UserSignupSettings(EnvironmentSettings):
    """
    Configuration for user signup role assignment.

    These settings control which roles are automatically assigned to users
    when they first authenticate with the platform.
    """

    model_config = EnvironmentSettings.create_settings_config("AIHUB_USER_SIGNUP_")

    REGULAR_USER_ROLES: Annotated[
        str,
        Field(
            description=(
                "Comma-separated list of roles assigned to regular users (not the first user). "
                "These users typically have standard platform access."
            ),
        ),
    ] = "AIHubUser"

    FIRST_ADMIN_USER_ROLES: Annotated[
        str,
        Field(
            description=(
                "Comma-separated list of roles assigned to the very first user. "
                "This user is typically the initial platform administrator."
            ),
        ),
    ] = "AIHubAdmin,AIHubUser"  # aihub.admin.> and aihub.user.> are separate hierarchies

    @computed_field
    @property
    def regular_user_roles_list(self) -> list[str]:
        """Returns the regular user signup roles as a list."""
        return [r.strip() for r in self.REGULAR_USER_ROLES.split(",") if r.strip()]

    @computed_field
    @property
    def first_admin_user_roles_list(self) -> list[str]:
        """Returns the first admin user signup roles as a list."""
        return [r.strip() for r in self.FIRST_ADMIN_USER_ROLES.split(",") if r.strip()]
