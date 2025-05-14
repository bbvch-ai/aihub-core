import logging
from typing import List

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

    def __init__(self, bearer_handlers: List[BearerAuthHandler], oauth2_handlers: List[OAuth2AuthHandler]):
        self.bearer_handlers = bearer_handlers
        self.oauth2_handlers = oauth2_handlers

    async def __call__(
        self,
        request: Request,
        bearer_token: HTTPAuthorizationCredentials | None = Security(HTTPBearer(auto_error=False)),
        oauth_token: str | None = Security(OAuth2Config().OPTIONAL_SCHEMA),
    ) -> AuthenticatedUser:
        errors = []

        for oauth2_handler in self.oauth2_handlers:
            try:
                return await oauth2_handler(oauth_token)
            except Exception as e:
                logger.warning(f"OAuth2 authentication {oauth2_handler.__class__.__name__} failed: {e}")
                errors.append(f"OAuth2 authentication {{oauth2_handler.__class__.__name__}} failed: {str(e)}")

        for bearer_handler in self.bearer_handlers:
            try:
                return await bearer_handler(request, bearer_token)
            except Exception as e:
                logger.warning(f"Bearer authentication {bearer_handler.__class__.__name__} failed: {e}")
                errors.append(f"Bearer authentication {bearer_handler.__class__.__name__} failed: {str(e)}")

        # If no strategy succeeded, raise an error with all failure details.
        logger.exception("Authentication failed for both OAuth2 and Bearer: %s", errors)
        raise HTTPException(status_code=401, detail=" | ".join(errors))

    async def authenticate_token(self, token: str) -> AuthenticatedUser:
        """
        Attempts to authenticate with the provided token using both OAuth2 and Bearer strategies.
        """
        errors = []

        for oauth2_handler in self.oauth2_handlers:
            try:
                return await oauth2_handler.authenticate_token(token)
            except Exception as e:
                logger.warning(f"OAuth2 authentication {oauth2_handler.__class__.__name__} failed: {e}")
                errors.append(f"OAuth2 authentication {{oauth2_handler.__class__.__name__}} failed: {str(e)}")

        for bearer_handler in self.bearer_handlers:
            try:
                return await bearer_handler.authenticate_token(token)
            except Exception as e:
                logger.warning(f"Bearer authentication {bearer_handler.__class__.__name__} failed: {e}")
                errors.append(f"Bearer authentication {bearer_handler.__class__.__name__} failed: {str(e)}")

        # If no strategy succeeded, raise an error with all failure details.
        logger.exception("Authentication failed for both OAuth2 and Bearer: %s", errors)
        raise HTTPException(status_code=401, detail=" | ".join(errors))
