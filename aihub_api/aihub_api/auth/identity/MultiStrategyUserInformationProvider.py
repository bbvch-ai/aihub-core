import logging

from aihub_api.auth.identity.BaseUserInformationProvider import BaseUserInformationProvider
from aihub_api.auth.identity.UserIdentity import UserIdentity


class MultiStrategyUserInformationProvider(BaseUserInformationProvider):
    """
    A composite user information provider that aggregates multiple base providers.

    It tries each provided user information provider in sequence. If one provider fails to fetch
    user details (by raising an exception), it moves on to the next. If all providers fail, it raises
    an exception with information about all failures.
    """

    def __init__(self, *providers: BaseUserInformationProvider):
        """Initializes the composite provider with a list of base providers."""
        if len(providers) == 0:
            raise ValueError("At least one user information provider must be provided.")
        self.providers = providers

    async def get_user_info_by_oid(self, oid: str) -> UserIdentity:
        """Attempts to fetch user information using the provided base providers in order."""
        errors = []
        for provider in self.providers:
            try:
                return await provider.get_user_info_by_oid(oid)
            except Exception as e:
                errors.append(f"{provider.__class__.__name__}: {str(e)}")

        error_message = f"All user information providers failed for oid '{oid}'. Errors: " + " | ".join(errors)
        raise PermissionError(error_message)
