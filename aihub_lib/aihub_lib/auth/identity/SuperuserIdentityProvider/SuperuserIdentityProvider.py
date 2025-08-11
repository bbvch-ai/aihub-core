from aihub_lib.auth.dependencies.SuperuserAuthHandler.SuperuserSettings import SuperuserSettings
from aihub_lib.auth.identity.IdentityProvider import IdentityProvider
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.user.UserEntity import UserEntity


class SuperuserIdentityProvider(IdentityProvider):
    """
    Identity provider that only supports the superuser
    """

    def __init__(self):
        self.config = SuperuserSettings()

    async def get_user_identity_by_oid(self, user_oid: str) -> UserIdentity:
        if user_oid != self.config.OID:
            raise ValueError(f"SuperuserIdentityProvider: oid '{user_oid}' " f"does not match the superuser oid.")
        user_identity = SuperuserSettings().get_user_identity()
        UserEntity.ensure_user_exists(
            oid=user_identity.id,
            name=user_identity.name,
            email=user_identity.email,
            roles=user_identity.roles,
            profile_image=user_identity.profile_image,
        )
        return user_identity

    async def get_user_identity_by_email(self, email: str) -> UserIdentity:
        if email != self.config.EMAIL:
            raise ValueError(f"SuperuserIdentityProvider: email '{email}' " f"does not match the superuser email.")
        user_identity = SuperuserSettings().get_user_identity()
        UserEntity.ensure_user_exists(
            oid=user_identity.id,
            name=user_identity.name,
            email=user_identity.email,
            roles=user_identity.roles,
            profile_image=user_identity.profile_image,
        )
        return user_identity

    async def get_user_roles(self, user_oid: str) -> list[str]:
        if user_oid != self.config.OID:
            raise ValueError(f"SuperuserIdentityProvider: oid '{user_oid}' " f"does not match the superuser oid.")
        return self.config.ROLES

    async def get_user_profile_image_data_url(self, user_oid: str) -> str | None:
        return None
