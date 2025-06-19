import logging

from fastapi import Request

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthConfig import DangerousDevelopmentOnlyAuthConfig
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import \
    DangerousDevelopmentOnlyIdentityProvider

logger = logging.getLogger(__name__)


class DangerousDevelopmentOnlyAuthHandler(AuthHandler):
    def __init__(self, identity_provider: DangerousDevelopmentOnlyIdentityProvider):
        super().__init__(identity_provider=identity_provider)
        self.config = DangerousDevelopmentOnlyAuthConfig()

    async def __call__(self, request: Request) -> AuthenticatedUser:
        return await self.authenticate_token("")

    async def authenticate_token(self, token_str: str) -> AuthenticatedUser:
        logger.warning("DangerousDevelopmentOnlyAuthHandler is active. This is not recommended for production use.")
        return AuthenticatedUser(
            name=self.config.NAME,
            preferred_username=self.config.EMAIL,
            oid=str(self.config.OID),
            roles=self.config.ROLES,
        )
