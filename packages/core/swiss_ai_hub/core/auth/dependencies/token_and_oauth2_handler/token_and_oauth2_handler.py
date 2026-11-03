import logging
from typing import NoReturn

from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler.keycloak_auth_handler import KeycloakAuthHandler
from swiss_ai_hub.core.auth.dependencies.open_webui_auth_handler.open_webui_auth_handler import OpenWebuiAuthHandler
from swiss_ai_hub.core.auth.dependencies.token_auth_handler.token_auth_handler import TokenAuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_settings import KeycloakSettings

logger = logging.getLogger(__name__)


class TokenAndOauth2Handler:
    """A composite authentication handler that sequentially attempts both OAuth2 and Bearer auth strategies."""

    def __init__(self, bearer_handlers: list[AuthHandler], oauth2_handlers: list[KeycloakAuthHandler]):
        self.bearer_handlers = bearer_handlers
        self.oauth2_handlers = oauth2_handlers

    async def __call__(
        self,
        request: Request,
        bearer_token: HTTPAuthorizationCredentials | None = Security(HTTPBearer(auto_error=False)),
        oauth_token: str | None = Security(KeycloakSettings().OPTIONAL_SCHEMA),
    ) -> UserIdentity:
        failures: list[tuple[str, Exception]] = []

        for bearer_handler in self.bearer_handlers:
            try:
                return await bearer_handler(request, bearer_token)
            except Exception as e:
                failures.append(self._log_failure("Bearer", bearer_handler, e))

        if oauth_token:
            for oauth2_handler in self.oauth2_handlers:
                try:
                    return await oauth2_handler.authenticate_token(oauth_token, request)
                except Exception as e:
                    failures.append(self._log_failure("OAuth2", oauth2_handler, e))

        self._raise_failure(failures)

    async def authenticate_token(self, token: str) -> UserIdentity:
        """Attempts to authenticate with the provided token using both OAuth2 and Bearer strategies."""
        failures: list[tuple[str, Exception]] = []

        for oauth2_handler in self.oauth2_handlers:
            try:
                return await oauth2_handler.authenticate_token(token)
            except Exception as e:
                failures.append(self._log_failure("OAuth2", oauth2_handler, e))

        for bearer_handler in self.bearer_handlers:
            try:
                return await bearer_handler.authenticate_token(token)
            except Exception as e:
                failures.append(self._log_failure("Bearer", bearer_handler, e))

        self._raise_failure(failures)

    @staticmethod
    def _log_failure(scheme: str, handler: object, error: Exception) -> tuple[str, Exception]:
        message = f"{scheme} authentication {handler.__class__.__name__} failed: {error}"
        logger.warning(message)
        return message, error

    @staticmethod
    def _raise_failure(failures: list[tuple[str, Exception]]) -> NoReturn:
        """A 403 is only raised after a handler has accepted the credentials — tenant access is resolved
        once the user is known — so it is the actual answer. Folding it into the combined 401 would tell
        the client its login failed when it is in fact not allowed into the requested tenant."""
        for _, error in failures:
            if isinstance(error, HTTPException) and error.status_code == status.HTTP_403_FORBIDDEN:
                raise error

        messages = [message for message, _ in failures]
        logger.error("Authentication failed for both OAuth2 and Bearer: %s", messages)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=" | ".join(messages))

    @classmethod
    def from_auth_settings(cls):
        bearer_handlers: list[AuthHandler] = []
        oauth2_handlers: list[KeycloakAuthHandler] = []

        oauth2_handlers.append(KeycloakAuthHandler())

        logger.info("Using token authentication")
        token_handler = TokenAuthHandler()
        bearer_handlers.append(OpenWebuiAuthHandler(base_auth_handler=token_handler))
        bearer_handlers.append(token_handler)

        return cls(
            bearer_handlers=bearer_handlers,
            oauth2_handlers=oauth2_handlers,
        )
