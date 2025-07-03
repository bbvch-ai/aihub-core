from typing import List, Optional

from aihub_lib.auth.identity.IdentityProvider import IdentityProvider
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.user.UserEntity import UserEntity


class TokenIdentityProvider(IdentityProvider):
    """
    A user information provider that retrieves user details from your own MongoDB database.

    This provider:
    - Searches for a `BearerToken` document where the embedded `ApiUser` has a matching OID.
    - Constructs a `UserIdentity` from the `ApiUser` data.

    Raises an exception if no matching user is found.
    """

    async def get_user_identity_by_oid(self, user_oid: str) -> UserIdentity:
        user = UserEntity.by_oid(user_oid)
        if user is None:
            raise ValueError(f"User with oid '{user_oid}' not found in the database.")

        return UserIdentity(
            id=user.id,
            name=user.name,
            email=user.email,
            profile_image=user.profile_image,
            roles=user.roles,
        )

    async def get_user_identity_by_email(self, email: str) -> UserIdentity:
        user = UserEntity.by_email(email)
        if user is None:
            raise ValueError(f"User with email '{email}' not found in the database.")

        return UserIdentity(
            id=user.id,
            name=user.name,
            email=user.email,
            profile_image=user.profile_image,
            roles=user.roles,
        )

    async def get_user_roles(self, user_oid: str) -> List[str]:
        user = await self.get_user_identity_by_oid(user_oid)
        return user.roles

    async def get_user_profile_image_data_url(self, user_oid: str) -> Optional[str]:
        user = await self.get_user_identity_by_oid(user_oid)
        return user.profile_image
