from api_core.auth.AuthenticatedUser import AuthenticatedUser
from api_core.auth.identity.azure.AzureUserInformationProvider import AzureUserInformationProvider
from api_core.routes.user.dto.UserDTO import UserDTO


class UserService:
    user_information_provider = AzureUserInformationProvider()

    @staticmethod
    def get_logged_in_user(user: AuthenticatedUser) -> UserDTO:
        return UserDTO.from_authenticated_user(user)

    @staticmethod
    def get_user_by_oid(user_oid: str) -> UserDTO:
        return UserService.user_information_provider.get_user_info_by_oid(user_oid)