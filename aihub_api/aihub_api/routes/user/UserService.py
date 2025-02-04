from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser

from aihub_api.auth.identity.azure.AzureUserInformationProvider import AzureUserInformationProvider
from aihub_api.routes.user.dto.UserDTO import UserDTO


class UserService:
    """
    A service layer that encapsulates user-related logic:
    - Converting an authenticated user object to a UserDTO.
    - Retrieving user information from Azure AD or another identity provider.

    ### Why UserService?
    By separating user logic from controllers, the code remains organized and testable.
    `UserService`:
    - Uses `AzureUserInformationProvider` to fetch user details by OID.
    - Converts `AuthenticatedUser` objects into `UserDTO`s for consistent responses.

    ### Methods
    - `get_logged_in_user`: Converts the currently authenticated user into a `UserDTO`.
    - `get_user_by_oid`: Retrieves a user's info by their OID (Object ID), useful for building responses that include user details.
    """

    user_information_provider = AzureUserInformationProvider()

    @staticmethod
    def get_logged_in_user(user: AuthenticatedUser) -> UserDTO:
        """
        Convert the `AuthenticatedUser` (provided by the auth layer) into a UserDTO.
        This usually includes fields like name, email, and OID.
        """
        return UserDTO.from_authenticated_user(user)

    @staticmethod
    def get_user_by_oid(user_oid: str) -> UserDTO:
        """
        Retrieve user info by OID from the user information provider.
        This allows integration with external identity systems like Azure AD.
        """
        return UserService.user_information_provider.get_user_info_by_oid(user_oid)
