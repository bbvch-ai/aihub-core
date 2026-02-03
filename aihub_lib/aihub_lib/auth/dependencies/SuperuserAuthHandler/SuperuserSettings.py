from typing import Annotated, Self

from pydantic import Field, SecretStr, computed_field, model_validator

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class SuperuserSettings(EnvironmentSettings):
    """
    Configuration for a global superuser that has access to everything.

    When ENABLED is False, credentials are optional.
    When ENABLED is True, all credentials (NAME, EMAIL, OID, TOKEN) must be provided.
    """

    model_config = EnvironmentSettings.create_settings_config("SUPERUSER_")

    ENABLED: Annotated[bool, Field(description="Whether the superuser is enabled.")] = False
    NAME: Annotated[str | None, Field(description="The user's displayed name.")] = None
    EMAIL: Annotated[
        str | None,
        Field(
            description="The user's email (often used as a login or unique identifier).",
        ),
    ] = None
    OID: Annotated[
        str | None,
        Field(
            description="A unique OID (Object ID) for the user.",
        ),
    ] = None
    ROLE: Annotated[str, Field(description="The role the superuser possesses.")] = "AIHubSuperuser"
    TOKEN: Annotated[SecretStr | None, Field(description="The superuser's access token.")] = None

    @model_validator(mode="after")
    def validate_credentials_when_enabled(self) -> Self:
        """If superuser is enabled, all credentials must be provided."""
        if not self.ENABLED:
            return self

        missing = []
        if not self.NAME:
            missing.append("SUPERUSER_NAME")
        if not self.EMAIL:
            missing.append("SUPERUSER_EMAIL")
        if not self.OID:
            missing.append("SUPERUSER_OID")
        if not self.TOKEN:
            missing.append("SUPERUSER_TOKEN")

        if missing:
            raise ValueError(f"Superuser is enabled but missing required settings: {', '.join(missing)}")

        return self

    @computed_field
    @property
    def ROLES(self) -> list[str]:
        return [self.ROLE]

    def get_user_identity(self, tenant) -> UserIdentity:
        """
        Create a UserIdentity for the superuser with the given tenant context.

        Only callable when ENABLED is True (validator ensures credentials are set).
        """
        # Validator guarantees these are set when ENABLED=True
        return UserIdentity(
            name=self.NAME,  # type: ignore[arg-type]
            email=self.EMAIL,  # type: ignore[arg-type]
            id=self.OID,  # type: ignore[arg-type]
            roles=self.ROLES,
            acting_within_tenant=tenant,
        )
