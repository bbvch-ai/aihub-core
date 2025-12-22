import logging

from fastapi import Request

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.auth.identity.UserIdentity import UserIdentity

logger = logging.getLogger(__name__)


class DangerousDevelopmentOnlyAuthHandler:
    """
    A FastAPI dependency for development/testing only.

    Bypasses all authentication and returns a fake user identity from configuration.
    WARNING: Never use in production!
    """

    def __init__(self) -> None:
        self.config = DangerousDevelopmentOnlyAuthSettings()

    async def __call__(self, request: Request) -> UserIdentity:
        return await self.authenticate_token("")

    async def authenticate_token(self, token_str: str) -> UserIdentity:
        """Returns fake dev user identity - no actual authentication."""
        logger.warning("DangerousDevelopmentOnlyAuthHandler is active. This is not recommended for production use.")
        return UserIdentity(
            id=self.config.OID,
            name=self.config.NAME,
            email=self.config.EMAIL,
            roles=self.config.ROLES,
            profile_image=None,
        )
