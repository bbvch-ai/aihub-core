from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import NoDecode

from aihub_lib.auth.identity.TenantIdentity import TenantIdentity
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class DangerousDevelopmentOnlyAuthSettings(EnvironmentSettings):
    """
    Configuration for the no-auth scenario, which provides a static user profile
    without requiring any actual authentication.

    ### Why This Config?
    In development or testing environments, you might not have a fully configured
    authentication system. `DangerousDevelopmentOnlyAuthSettings` allows you to proceed without authentication
    by supplying a fake user identity, ensuring your code can run and be tested even
    before the authentication integration is complete.
    """

    model_config = EnvironmentSettings.create_settings_config("DANGEROUS_DEV_ONLY_AUTH_FAKE_")

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
            description="A unique OID (Object ID) for the user. Defaults to a UUID.",
        ),
    ]
    ROLES: Annotated[list[str], NoDecode, Field(description="A list of roles this user possesses.")]

    @field_validator("ROLES", mode="before")
    @classmethod
    def decode_roles(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, list):
            return v
        return v.split(",")

    def get_user_identity(self) -> UserIdentity:
        return UserIdentity(
            name=DangerousDevelopmentOnlyAuthSettings().NAME,
            email=DangerousDevelopmentOnlyAuthSettings().EMAIL,
            id=DangerousDevelopmentOnlyAuthSettings().OID,
            roles=DangerousDevelopmentOnlyAuthSettings().ROLES,
            acting_within_tenant=TenantIdentity(
                id="__dangerous_development_only_tenant__",
                name="Dangerous Development Only Tenant",
                access_rules=["aihub.admin.>"],
            ),
        )
