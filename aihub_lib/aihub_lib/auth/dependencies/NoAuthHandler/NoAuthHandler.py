import logging

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthConfig import NoAuthConfig

from fastapi import Request


logger = logging.getLogger(__name__)

class NoAuthHandler(AuthHandler):
    def __init__(self):
        self.config = NoAuthConfig()

    async def __call__(self, request: Request) -> AuthenticatedUser:
        logger.warning("NoAuthHandler is active. This is not recommended for production use.")
        return AuthenticatedUser(
            name=self.config.NAME,
            preferred_username=self.config.EMAIL,
            oid=str(self.config.OID),
            roles=self.config.ROLES,
        )