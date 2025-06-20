from typing import List, Optional

from aihub_lib.auth.identity.IdentityProvider import IdentityProvider
from aihub_lib.auth.identity.UserIdentity import UserIdentity


class MultiStrategyTokenIdentityProvider(IdentityProvider):
    """
    A composite user information provider that aggregates multiple base providers.

    It tries each provided user information provider in sequence. If one provider fails to fetch
    user details (by raising an exception), it moves on to the next. If all providers fail, it raises
    an exception with information about all failures.
    """

    def __init__(self, *providers: IdentityProvider):
        """Initializes the composite provider with a list of base providers."""
        if len(providers) == 0:
            raise ValueError("At least one user information provider must be provided.")
        self.providers = providers

    async def get_user_info_by_oid(self, oid: str) -> UserIdentity:
        """Attempts to fetch user information using the provided base providers in order."""

    async def get_user_identity_by_oid(self, user_oid: str) -> UserIdentity:
        errors = []
        for provider in self.providers:
            try:
                return await provider.get_user_identity_by_oid(user_oid)
            except Exception as e:
                errors.append(f"{provider.__class__.__name__}: {str(e)}")

        error_message = f"All user information providers failed for oid '{user_oid}'. Errors: " + " | ".join(errors)
        raise PermissionError(error_message)

    async def get_user_identity_by_email(self, email: str) -> UserIdentity:
        errors = []
        for provider in self.providers:
            try:
                return await provider.get_user_identity_by_email(email)
            except Exception as e:
                errors.append(f"{provider.__class__.__name__}: {str(e)}")

        error_message = f"All user email providers failed for email '{email}'. Errors: " + " | ".join(errors)
        raise PermissionError(error_message)

    async def get_user_roles(self, user_oid: str) -> List[str]:
        errors = []
        for provider in self.providers:
            try:
                return await provider.get_user_roles(user_oid)
            except Exception as e:
                errors.append(f"{provider.__class__.__name__}: {str(e)}")

        error_message = f"All user role providers failed for oid '{user_oid}'. Errors: " + " | ".join(errors)
        raise PermissionError(error_message)

    async def get_user_profile_image_data_url(self, user_oid: str) -> Optional[str]:
        errors = []
        for provider in self.providers:
            try:
                return await provider.get_user_profile_image_data_url(user_oid)
            except Exception as e:
                errors.append(f"{provider.__class__.__name__}: {str(e)}")

        error_message = f"All user image providers failed for oid '{user_oid}'. Errors: " + " | ".join(errors)
        raise PermissionError(error_message)