from aihub_lib.auth.dependencies.SuperuserAuthHandler.SuperuserSettings import SuperuserSettings
from aihub_lib.auth.identity.IdentityProvider import IdentityProvider
from aihub_lib.auth.identity.UserIdentity import UserIdentity


class SuperuserIdentityProvider(IdentityProvider):
    """
    Identity provider that only supports the superuser
    """

    def __init__(self):
        self.config = SuperuserSettings()

    async def get_user_identity_by_oid(self, user_oid: str) -> UserIdentity:
        if user_oid != self.config.OID:
            raise ValueError(f"SuperuserIdentityProvider: oid '{user_oid}' does not match the superuser oid.")
        return self.config.get_user_identity()

    async def get_user_identity_by_email(self, email: str) -> UserIdentity:
        if email != self.config.EMAIL:
            raise ValueError(f"SuperuserIdentityProvider: email '{email}' does not match the superuser email.")
        return self.config.get_user_identity()

    async def get_user_roles(self, user_oid: str) -> list[str]:
        if user_oid != self.config.OID:
            raise ValueError(f"SuperuserIdentityProvider: oid '{user_oid}' does not match the superuser oid.")
        return self.config.ROLES

    async def get_user_profile_image_data_url(self, user_oid: str) -> str | None:
        return None
