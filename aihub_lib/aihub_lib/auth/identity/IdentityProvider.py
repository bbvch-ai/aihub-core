from abc import ABC, abstractmethod

from aihub_lib.auth.identity.UserIdentity import UserIdentity


class IdentityProvider(ABC):
    """
    Abstract base class for retrieving user information from an identity provider by a user's OID.

    ### Why This Interface?
    By defining a common interface for user information retrieval, different implementations
    (e.g., Microsoft Graph, a custom IDP, or a mock provider) can be swapped without affecting
    the rest of the codebase. This ensures flexibility in choosing or changing identity services.
    """

    @abstractmethod
    async def get_user_identity_by_oid(self, user_oid: str) -> UserIdentity:
        pass

    @abstractmethod
    async def get_user_identity_by_email(self, email: str) -> UserIdentity:
        pass

    @abstractmethod
    async def get_user_roles(self, user_oid: str) -> list[str]:
        pass

    @abstractmethod
    async def get_user_profile_image_data_url(self, user_oid: str) -> str | None:
        pass
