from api_core.auth.AuthenticatedUser import AuthenticatedUser
from api_core.routes.user.dto.UserDTO import UserDTO


class UserService:

    @staticmethod
    def get_user(user: AuthenticatedUser) -> UserDTO:
        return UserDTO.from_authenticated_user(user)