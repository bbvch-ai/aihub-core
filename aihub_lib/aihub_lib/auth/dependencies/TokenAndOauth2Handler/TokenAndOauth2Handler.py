import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.BearerAuthHandler import BearerAuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Config import OAuth2Config

logger = logging.getLogger(__name__)


class TokenAndOauth2Handler(AuthHandler):
    """A composite authentication handler that sequentially attempts both OAuth2 and Bearer auth strategies."""

    def __init__(self, bearer_handler: BearerAuthHandler, oauth2_handler: OAuth2AuthHandler):
        self.bearer_handler = bearer_handler
        self.oauth2_handler = oauth2_handler

    async def __call__(
        self,
        request: Request,
        bearer_token: HTTPAuthorizationCredentials | None = Security(HTTPBearer(auto_error=False)),
        oauth_token: str | None = Security(OAuth2Config().OPTIONAL_SCHEMA),
    ) -> AuthenticatedUser:
        errors = []

        try:
            return await self.oauth2_handler(oauth_token)
        except Exception as e:
            logger.warning("OAuth2 authentication failed: %s", e)
            errors.append(f"OAuth2 authentication failed: {str(e)}")

        try:
            return await self.bearer_handler(request, bearer_token)
        except Exception as e:
            logger.warning("Bearer authentication failed: %s", e)
            errors.append(f"Bearer authentication failed: {str(e)}")

        # If no strategy succeeded, raise an error with all failure details.
        logger.exception("Authentication failed for both OAuth2 and Bearer: %s", errors)
        raise HTTPException(status_code=401, detail=" | ".join(errors))

    async def authenticate_token(self, token: str) -> AuthenticatedUser:
        """
        Attempts to authenticate with the provided token using both OAuth2 and Bearer strategies.
        """
        errors = []

        # Try OAuth2 first
        try:
            return await self.oauth2_handler.authenticate_token(token)
        except Exception as e:
            logger.warning("OAuth2 authentication failed: %s", e)
            errors.append(f"OAuth2 authentication failed: {str(e)}")

        # Then try Bearer token
        try:
            # Create a mock request for the bearer handler
            return await self.bearer_handler.authenticate_token(token)
        except Exception as e:
            logger.warning("Bearer authentication failed: %s", e)
            errors.append(f"Bearer authentication failed: {str(e)}")

        # If no strategy succeeded, raise an error with all failure details.
        logger.exception("Authentication failed for both OAuth2 and Bearer: %s", errors)
        raise HTTPException(status_code=401, detail=" | ".join(errors))
