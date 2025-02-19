from aihub_lib.persistence.access.entities.BearerToken import BearerToken

from aihub_api.auth.identity.BaseUserInformationProvider import BaseUserInformationProvider
from aihub_api.routes.user.dto.UserDTO import UserDTO


class ApiTokenUserInformationProvider(BaseUserInformationProvider):
    """
    A user information provider that retrieves user details from your own MongoDB database.

    This provider:
    - Searches for a `BearerToken` document where the embedded `ApiUser` has a matching OID.
    - Constructs a `UserDTO` from the `ApiUser` data.

    Raises an exception if no matching user is found.
    """

    def get_user_info_by_oid(self, oid: str) -> UserDTO:
        """Fetch user information from your MongoDB database using an OID."""
        token_obj = BearerToken.objects(user__oid=oid).first()
        if token_obj is None:
            raise ValueError(f"User with oid '{oid}' not found in the database.")

        api_user = token_obj.user
        return UserDTO(
            id=api_user.oid,
            name=api_user.name,
            email=api_user.preferred_username,  # assuming preferred_username holds the email address
        )
