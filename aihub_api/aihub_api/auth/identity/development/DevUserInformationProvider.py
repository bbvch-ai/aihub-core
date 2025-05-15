from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthConfig import NoAuthConfig

from aihub_api.auth.identity.BaseUserInformationProvider import BaseUserInformationProvider
from aihub_api.auth.identity.UserIdentity import UserIdentity


class DevUserInformationProvider(BaseUserInformationProvider):
    """
    A developer user information provider that returns a fixed user identity from the NoAuthConfig.

    It checks if the provided oid matches the configured dev oid and, if so, returns a UserIdentity
    built from the configuration settings. This is useful in development or testing environments
    where authentication may be bypassed.
    """

    def __init__(self):
        self.config = NoAuthConfig()

    async def get_user_info_by_oid(self, oid: str) -> UserIdentity:
        if oid == self.config.OID:
            return UserIdentity(
                id=self.config.OID,
                name=self.config.NAME,
                email=self.config.EMAIL,
                roles=self.config.ROLES,
            )
        raise Exception(
            f"DevUserInformationProvider: oid '{oid}' does not match the configured dev oid '{self.config.OID}'."
        )
