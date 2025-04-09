from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser

from aihub_api.auth.identity.api.ApiTokenUserInformationProvider import ApiTokenUserInformationProvider
from aihub_api.auth.identity.azure.AzureUserInformationProvider import AzureUserInformationProvider
from aihub_api.auth.identity.development.DevUserInformationProvider import DevUserInformationProvider
from aihub_api.auth.identity.MultiStrategyUserInformationProvider import MultiStrategyUserInformationProvider
from aihub_api.routes.user.dto.MyUserDTO import MyUserDTO
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

    user_information_provider = MultiStrategyUserInformationProvider(
        DevUserInformationProvider(),
        AzureUserInformationProvider(),
        ApiTokenUserInformationProvider(),
    )

    @staticmethod
    def get_logged_in_user(user: AuthenticatedUser) -> MyUserDTO:
        """
        Convert the `AuthenticatedUser` (provided by the auth layer) into a MyUserDTO.
        This usually includes fields like name, email, and OID.
        """
        user = UserService.get_user_by_oid(user.oid)
        return MyUserDTO(
            id=user.id,
            name=user.name,
            email=user.email,
            profile_image=user.profile_image,
        )

    @staticmethod
    def get_user_by_oid(user_oid: str) -> UserDTO:
        """
        Retrieve user info by OID from the user information provider.
        This allows integration with external identity systems like Azure AD.
        """
        return UserService.user_information_provider.get_user_info_by_oid(user_oid)
