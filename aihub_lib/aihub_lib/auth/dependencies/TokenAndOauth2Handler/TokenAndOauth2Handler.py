import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.AuthSettings import AuthSettings
from aihub_lib.auth.dependencies.BearerAuthHandler import BearerAuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Settings import OAuth2Settings
from aihub_lib.auth.dependencies.OpenWebuiAuthHandler.OpenWebuiAuthHandler import OpenWebuiAuthHandler
from aihub_lib.auth.dependencies.SuperuserAuthHandler.SuperuserAuthHandler import SuperuserAuthHandler
from aihub_lib.auth.dependencies.SuperuserAuthHandler.SuperuserSettings import SuperuserSettings
from aihub_lib.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler
from aihub_lib.auth.identity.AzureIdentityProvider.AzureIdentityProvider import AzureIdentityProvider
from aihub_lib.auth.identity.IdentityProvider import IdentityProvider
from aihub_lib.auth.identity.MultiStrategyIdentityProvider.MultiStrategyIdentityProvider import (
    MultiStrategyIdentityProvider,
)
from aihub_lib.auth.identity.SuperuserIdentityProvider.SuperuserIdentityProvider import SuperuserIdentityProvider
from aihub_lib.auth.identity.TokenIdentityProvider.TokenIdentityProvider import TokenIdentityProvider
from aihub_lib.auth.identity.UserIdentity import UserIdentity

logger = logging.getLogger(__name__)


class TokenAndOauth2Handler(AuthHandler):
    """A composite authentication handler that sequentially attempts both OAuth2 and Bearer auth strategies."""

    def __init__(self, bearer_handlers: list[BearerAuthHandler], oauth2_handlers: list[OAuth2AuthHandler]):
        self.bearer_handlers = bearer_handlers
        self.oauth2_handlers = oauth2_handlers

    @property
    def identity_provider(self) -> IdentityProvider:
        identity_providers = []
        for oauth2_handler in self.oauth2_handlers:
            identity_providers.append(oauth2_handler.identity_provider)
        for bearer_handler in self.bearer_handlers:
            identity_providers.append(bearer_handler.identity_provider)
        return MultiStrategyIdentityProvider(*identity_providers)

    async def __call__(
        self,
        request: Request,
        bearer_token: HTTPAuthorizationCredentials | None = Security(HTTPBearer(auto_error=False)),
        oauth_token: str | None = Security(OAuth2Settings().OPTIONAL_SCHEMA),
    ) -> UserIdentity:
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

    async def authenticate_token(self, token: str) -> UserIdentity:
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

    @classmethod
    def from_auth_settings(cls):
        bearer_handlers: list[BearerAuthHandler] = []
        oauth2_handlers: list[OAuth2AuthHandler] = []

        config = AuthSettings()

        if config.IDENTITY_PROVIDER == "azure":
            logger.info("Using Azure identity provider")
            identity_provider = AzureIdentityProvider()
            oauth2_handlers.append(
                OAuth2AuthHandler(identity_provider=identity_provider),
            )
        else:
            raise ValueError(f"Unknown identity provider: {config.IDENTITY_PROVIDER}")

        if SuperuserSettings().ENABLED:
            logger.info("Using superuser identity provider")
            bearer_handlers.append(
                SuperuserAuthHandler(identity_provider=SuperuserIdentityProvider()),
            )
            bearer_handlers.append(
                OpenWebuiAuthHandler(
                    identity_provider=identity_provider,
                    base_auth_handler=SuperuserAuthHandler(identity_provider=SuperuserIdentityProvider()),
                ),
            )

        if config.ENABLE_API_ACCESS:
            logger.info("Using token identity provider")
            bearer_handlers.append(
                TokenAuthHandler(identity_provider=TokenIdentityProvider()),
            )
            bearer_handlers.append(
                OpenWebuiAuthHandler(
                    identity_provider=identity_provider,
                    base_auth_handler=TokenAuthHandler(identity_provider=TokenIdentityProvider()),
                ),
            )

        return cls(
            bearer_handlers=bearer_handlers,
            oauth2_handlers=oauth2_handlers,
        )
