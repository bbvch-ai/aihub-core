import hashlib
import logging
from typing import Annotated, ClassVar

import jwt
from fastapi import HTTPException, Request

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.auth.realm_roles import SYS_ADMIN_ROLE
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_session_lookup import OpenWebuiSessionLookup
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_settings import OpenWebuiSettings

logger = logging.getLogger(__name__)

_NOT_SIGNED_IN = "Not signed in to OpenWebUI."


class OpenWebuiSessionAuthHandler(AuthHandler):
    """Identifies who views something OpenWebUI renders from its own origin, such as a figure in a source.

    A URL there carries no credential; the browser sends OpenWebUI's session cookie with it, and OpenWebUI says whose
    it is. Like the signed-header handler, it never grants the sysadmin bypass. Identities are cached by the token's
    hash for a minute, because one source can hold many figures.
    """

    SESSION_COOKIE: ClassVar[str] = "token"
    API_KEY_PREFIX: ClassVar[str] = "sk-"
    MAX_TOKEN_LENGTH: ClassVar[int] = 4096
    CACHE_SECONDS: ClassVar[int] = 60
    _CACHE_PREFIX: ClassVar[str] = "openwebui_session_identity:"
    _REJECTED: ClassVar[str] = ""
    _TOKEN_ALGORITHMS: ClassVar[list[str]] = ["HS256"]

    def __init__(self, session_lookup: OpenWebuiSessionLookup | None = None, secret_key: str | None = None) -> None:
        self._session_lookup = session_lookup
        self._secret_key = secret_key

    async def __call__(self, request: Request) -> UserIdentity:
        token = request.cookies.get(self.SESSION_COOKIE)
        if not self._is_signed_session_token(token):
            raise self._not_signed_in()

        redis = request.app.state.redis
        cache_key = self._cache_key(token, request)
        cached = await redis.get(cache_key)
        if cached is not None:
            if self._as_text(cached) == self._REJECTED:
                raise self._not_signed_in()
            return UserIdentity.model_validate_json(cached)

        email = await self._lookup().email_of(token)
        if email is None:
            await redis.set(cache_key, self._REJECTED, ex=self.CACHE_SECONDS)
            raise self._not_signed_in()

        identity = await self._identity_for(email, request)
        await redis.set(cache_key, identity.model_dump_json(), ex=self.CACHE_SECONDS)
        return identity

    async def authenticate_token(self, token: str, request: Request | None = None) -> UserIdentity:
        """The session cookie only identifies a viewer of a request to OpenWebUI's origin."""
        raise NotImplementedError("OpenWebuiSessionAuthHandler authenticates requests, not bare tokens")

    async def _identity_for(self, email: str, request: Request) -> UserIdentity:
        keycloak_user = await KeycloakAdminService.find_user_by_email(email)
        if not keycloak_user or not keycloak_user.enabled:
            logger.warning("OpenWebUI session belongs to an e-mail without an enabled Keycloak user")
            raise self._not_signed_in()
        realm_roles = await KeycloakAdminService.get_user_realm_roles(keycloak_user.id)
        return await self.build_identity(
            user_id=keycloak_user.id,
            name=keycloak_user.name,
            email=keycloak_user.email,
            request=request,
            openwebui_sys_admin=SYS_ADMIN_ROLE in realm_roles,
        )

    def _is_signed_session_token(self, token: str | None) -> bool:
        """Checked locally before OpenWebUI is asked, so a forged cookie costs neither a call nor a cache entry.

        OpenWebUI still decides, because only it knows whether the session was signed out.
        """
        if not token or len(token) > self.MAX_TOKEN_LENGTH or token.startswith(self.API_KEY_PREFIX):
            return False
        try:
            jwt.decode(token, self._signing_key(), algorithms=self._TOKEN_ALGORITHMS)
        except jwt.InvalidTokenError:
            return False
        return True

    def _signing_key(self) -> str:
        if self._secret_key is None:
            self._secret_key = OpenWebuiSettings().SECRET_KEY.get_secret_value()
        return self._secret_key

    def _lookup(self) -> OpenWebuiSessionLookup:
        if self._session_lookup is None:
            self._session_lookup = OpenWebuiSessionLookup(OpenWebuiSettings().BASE_URL)
        return self._session_lookup

    @classmethod
    def _cache_key(
        cls, token: str, request: Request
    ) -> Annotated[str, "Per token and tenant: the identity carries the tenant's roles"]:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return f"{cls._CACHE_PREFIX}{token_hash}:{request.path_params.get('tenant_id', '')}"

    @staticmethod
    def _as_text(value: str | bytes) -> str:
        return value.decode() if isinstance(value, bytes) else value

    @staticmethod
    def _not_signed_in() -> HTTPException:
        return HTTPException(status_code=401, detail=_NOT_SIGNED_IN)
