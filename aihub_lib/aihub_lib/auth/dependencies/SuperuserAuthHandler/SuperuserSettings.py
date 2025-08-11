from typing import Annotated

from pydantic import Field, field_validator, computed_field
from pydantic_settings import NoDecode

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class SuperuserSettings(EnvironmentSettings):
    """
    Configuration for a global superuser that has access to everything.
    """

    model_config = EnvironmentSettings.create_settings_config("AIHUB_SUPERUSER_")

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
    ROLE: Annotated[list[str], NoDecode, Field(description="A list of roles this user possesses.")] = ["AIHubSuperuser"]
    TOKEN: Annotated[str, Field(description="The superuser's access token.")]

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
