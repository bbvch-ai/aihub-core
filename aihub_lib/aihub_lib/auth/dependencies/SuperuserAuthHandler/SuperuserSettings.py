from typing import Annotated

from pydantic import Field, SecretStr, computed_field, field_validator

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class SuperuserSettings(EnvironmentSettings):
    """
    Configuration for a global superuser that has access to everything.
    """

    model_config = EnvironmentSettings.create_settings_config("SUPERUSER_")

    ENABLED: Annotated[bool, Field(description="Whether the superuser is enabled.")] = True
    NAME: Annotated[str, Field(description="The user's displayed name.")]
    EMAIL: Annotated[
        str,
        Field(
            description="The user's email (often used as a login or unique identifier).",
        ),
    ]
    OID: Annotated[
        str,
        Field(
            description="A unique OID (Object ID) for the user.",
        ),
    ]
    ROLE: Annotated[str, Field(description="The role the superuser possesses.")] = "AIHubSuperuser"
    TOKEN: Annotated[SecretStr, Field(description="The superuser's access token.", min_length=64)]

    @field_validator("ROLES", mode="before")
    @classmethod
    def decode_roles(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, list):
            return v
        return v.split(",")

    @computed_field
    @property
    def ROLES(self) -> list[str]:
        return [self.ROLE]

    def get_user_identity(self) -> UserIdentity:
        return UserIdentity(
            name=SuperuserSettings().NAME,
            email=SuperuserSettings().EMAIL,
            id=SuperuserSettings().OID,
            roles=SuperuserSettings().ROLES,
        )
