from aihub_api.auth.identity.BaseUserInformationProvider import BaseUserInformationProvider
from aihub_api.routes.user.dto.UserDTO import UserDTO
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthConfig import NoAuthConfig


class DevUserInformationProvider(BaseUserInformationProvider):
    """
    A developer user information provider that returns a fixed user identity from the NoAuthConfig.

    It checks if the provided oid matches the configured dev oid and, if so, returns a UserDTO
    built from the configuration settings. This is useful in development or testing environments
    where authentication may be bypassed.
    """

    def __init__(self):
        self.config = NoAuthConfig()

    def get_user_info_by_oid(self, oid: str) -> UserDTO:
        if oid == self.config.OID:
            return UserDTO(
                id=self.config.OID,
                name=self.config.NAME,
                email=self.config.EMAIL,
            )
        raise Exception(
            f"DevUserInformationProvider: oid '{oid}' does not match the configured dev oid '{self.config.OID}'."
        )
