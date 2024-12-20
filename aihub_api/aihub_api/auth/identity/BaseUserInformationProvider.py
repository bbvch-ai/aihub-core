from abc import ABC, abstractmethod

from aihub_api.routes.user.dto.UserDTO import UserDTO


class BaseUserInformationProvider(ABC):
    """
    Abstract base class for retrieving user information from an identity provider by a user's OID.

    ### Why This Interface?
    By defining a common interface for user information retrieval, different implementations
    (e.g., Microsoft Graph, a custom IDP, or a mock provider) can be swapped without affecting
    the rest of the codebase. This ensures flexibility in choosing or changing identity services.

    ### Method
    - `get_user_info_by_oid(oid: str) -> UserDTO`:
      Given a user OID, return a `UserDTO` with user details like name and email.
    """

    @abstractmethod
    def get_user_info_by_oid(self, oid: str) -> UserDTO:
        """
        Retrieve user information from the identity provider using the user's OID.

        :param oid: The unique OID of the user in the identity provider.
        :return: A `UserDTO` instance containing user details (id, name, email).
        """
        pass
