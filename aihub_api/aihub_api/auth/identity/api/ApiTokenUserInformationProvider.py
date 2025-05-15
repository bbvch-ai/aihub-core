from aihub_lib.persistence.user.UserEntity import UserEntity

from aihub_api.auth.identity.BaseUserInformationProvider import BaseUserInformationProvider
from aihub_api.auth.identity.UserIdentity import UserIdentity


class ApiTokenUserInformationProvider(BaseUserInformationProvider):
    """
    A user information provider that retrieves user details from your own MongoDB database.

    This provider:
    - Searches for a `BearerToken` document where the embedded `ApiUser` has a matching OID.
    - Constructs a `UserIdentity` from the `ApiUser` data.

    Raises an exception if no matching user is found.
    """

    async def get_user_info_by_oid(self, oid: str) -> UserIdentity:
        """Fetch user information from your MongoDB database using an OID."""
        user = UserEntity.by_oid(oid)
        if user is None:
            raise ValueError(f"User with oid '{oid}' not found in the database.")

        return UserIdentity(
            id=user.id,
            name=user.name,
            email=user.email,
            profile_image=user.profile_image,
            roles=user.roles,
        )
