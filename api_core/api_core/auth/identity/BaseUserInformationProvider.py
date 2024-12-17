from abc import ABC, abstractmethod

from api_core.routes.user.dto.UserDTO import UserDTO


class BaseUserInformationProvider(ABC):
    """
    An abstract base class that defines the interface for fetching user information
    from an identity provider given a user's OID.
    """

    @abstractmethod
    def get_user_info_by_oid(self, oid: str) -> UserDTO:
        """
        Given a user's OID, return a dictionary of user information (e.g., name, email).
        """
        pass