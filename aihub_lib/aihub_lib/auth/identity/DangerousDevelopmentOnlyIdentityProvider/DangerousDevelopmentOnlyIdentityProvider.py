from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.auth.identity.IdentityProvider import IdentityProvider
from aihub_lib.auth.identity.UserIdentity import UserIdentity


class DangerousDevelopmentOnlyIdentityProvider(IdentityProvider):
    """
    A developer user information provider that returns a fixed user identity
    from the DangerousDevelopmentOnlyAuthSettings.

    It checks if the provided oid matches the configured dev oid and, if so, returns a UserIdentity
    built from the configuration settings. This is useful in development or testing environments
    where authentication may be bypassed.
    """

    def __init__(self):
        self.config = DangerousDevelopmentOnlyAuthSettings()

    async def get_user_identity_by_oid(self, user_oid: str) -> UserIdentity:
        if user_oid != self.config.OID:
            raise ValueError(
                f"DangerousDevelopmentOnlyIdentityProvider: oid '{user_oid}' "
                f"does not match the configured dev oid '{self.config.OID}'."
            )
        return self.config.get_user_identity()

    async def get_user_identity_by_email(self, email: str) -> UserIdentity:
        if email != self.config.EMAIL:
            raise ValueError(
                f"DangerousDevelopmentOnlyIdentityProvider: email '{email}' "
                f"does not match the configured dev email '{self.config.EMAIL}'."
            )
        return self.config.get_user_identity()

    async def get_user_roles(self, user_oid: str) -> list[str]:
        if user_oid != self.config.OID:
            raise ValueError(
                f"DangerousDevelopmentOnlyIdentityProvider: oid '{user_oid}' "
                f"does not match the configured dev oid '{self.config.OID}'."
            )
        return self.config.ROLES

    async def get_user_profile_image_data_url(self, user_oid: str) -> str | None:
        return None
