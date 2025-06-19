from abc import ABC, abstractmethod
from typing import List, Optional

from aihub_lib.auth.identity.UserIdentity import UserIdentity


class IdentityProvider(ABC):
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
    async def get_user_identity_by_oid(self, user_oid: str) -> UserIdentity:
        pass

    @abstractmethod
    async def get_user_identity_by_email(self, email: str) -> UserIdentity:
        pass

    @abstractmethod
    async def get_user_roles(self, user_oid: str) -> List[str]:
        pass

    @abstractmethod
    async def get_user_profile_image_data_url(self, user_oid: str) -> Optional[str]:
        pass
