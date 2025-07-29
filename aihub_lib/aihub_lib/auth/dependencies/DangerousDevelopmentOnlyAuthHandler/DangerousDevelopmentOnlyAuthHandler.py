import logging

from fastapi import Request

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.auth.identity.UserIdentity import UserIdentity

logger = logging.getLogger(__name__)


class DangerousDevelopmentOnlyAuthHandler(AuthHandler):
    def __init__(self, identity_provider: DangerousDevelopmentOnlyIdentityProvider):
        super().__init__(identity_provider=identity_provider)
        self.config = DangerousDevelopmentOnlyAuthSettings()

    async def __call__(self, request: Request) -> UserIdentity:
        return await self.authenticate_token("")

    async def authenticate_token(self, token_str: str) -> UserIdentity:
        logger.warning("DangerousDevelopmentOnlyAuthHandler is active. This is not recommended for production use.")
        return await self._identity_provider.get_user_identity_by_oid(self.config.OID)
