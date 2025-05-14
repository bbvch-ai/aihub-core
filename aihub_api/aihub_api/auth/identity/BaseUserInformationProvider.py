from abc import ABC, abstractmethod

from aihub_api.auth.identity.UserIdentity import UserIdentity


class BaseUserInformationProvider(ABC):
    """
    Abstract base class for retrieving user information from an identity provider by a user's OID.

    ### Why This Interface?
    By defining a common interface for user information retrieval, different implementations
    (e.g., Microsoft Graph, a custom IDP, or a mock provider) can be swapped without affecting
    the rest of the codebase. This ensures flexibility in choosing or changing identity services.

    ### Method
    - `get_user_info_by_oid(oid: str) -> UserIdentity`:
      Given a user OID, return a `UserIdentity` with user details like name and email.
    """

    @abstractmethod
    def get_user_info_by_oid(self, oid: str) -> UserIdentity:
        pass
