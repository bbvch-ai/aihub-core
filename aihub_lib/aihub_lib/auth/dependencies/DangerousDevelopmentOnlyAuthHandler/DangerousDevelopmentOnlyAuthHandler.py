import logging

from fastapi import Request

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.user.UserEntity import UserEntity

logger = logging.getLogger(__name__)


class DangerousDevelopmentOnlyAuthHandler(AuthHandler):
    """
    A FastAPI dependency for development/testing only.

    Bypasses all authentication and returns a fake user identity from configuration.
    WARNING: Never use in production!
    """

    def __init__(self) -> None:
        self.config = DangerousDevelopmentOnlyAuthSettings()

    async def __call__(self, request: Request) -> UserIdentity:
        return await self.authenticate_token("", request)

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        """
        Returns fake dev user identity - no actual authentication.

        Creates/updates the dev user in the database to ensure it exists for other parts of the codebase.
        """
        logger.warning("DangerousDevelopmentOnlyAuthHandler is active. This is not recommended for production use.")

        # Ensure the dev user exists in the database
        user_entity = UserEntity.ensure_user_exists_for_auth(
            oid=self.config.OID,
            name=self.config.NAME,
            email=self.config.EMAIL,
        )

        # Resolve tenant context from request or use default
        if request:
            tenant = self.resolve_tenant_for_user(request, user_entity.id)
        else:
            # Fallback for contexts without request
            tenant = self.get_default_tenant_for_user(user_entity.id)

        return UserIdentity.from_user_entity(user_entity, tenant)
