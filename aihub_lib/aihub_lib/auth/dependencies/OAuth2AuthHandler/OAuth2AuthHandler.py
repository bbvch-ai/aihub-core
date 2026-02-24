import logging

import httpx
import jwt
from cachetools import TTLCache
from fastapi import HTTPException, Request, Security
from jwt.algorithms import RSAAlgorithm

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Settings import OAuth2Settings
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.user.UserEntity import UserEntity

logger = logging.getLogger(__name__)


class OAuth2AuthHandler(AuthHandler):
    """
    A FastAPI dependency for OAuth2 authentication via Azure AD.

    Validates JWT tokens. User data is extracted directly from JWT claims.
    """

    _jwks_cache: TTLCache = TTLCache(maxsize=100, ttl=21600)
    _rsa_key_cache: TTLCache = TTLCache(maxsize=10, ttl=21600)

    def __init__(self):
        self.config = OAuth2Settings()

    async def __call__(self, request: Request, oauth_token: str = Security(OAuth2Settings().SCHEMA)) -> UserIdentity:
        return await self.authenticate_token(oauth_token, request)

    async def _get_jwks(self) -> dict:
        """Retrieves the JWKS from the configured URL, using caching to minimize API calls."""
        cache_key = "jwks"
        if cache_key in self._jwks_cache:
            return self._jwks_cache[cache_key]

        try:
            logger.debug("JWKS cache miss, fetching from %s", OAuth2Settings().JWKS_URL)
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=30.0, read=10.0)) as client:
                jwks_response = await client.get(OAuth2Settings().JWKS_URL)
                jwks_response.raise_for_status()
                jwks = jwks_response.json()
                self._jwks_cache[cache_key] = jwks
                return jwks
        except httpx.HTTPError as e:
            logger.exception("Error fetching JWKS: %s", str(e))
            raise HTTPException(status_code=500, detail="Authentication service unavailable")

    async def _get_rsa_key(self, kid: str) -> object | None:
        """Gets an RSA key for the specified key ID (kid)."""
        if kid in self._rsa_key_cache:
            return self._rsa_key_cache[kid]

        jwks = await self._get_jwks()

        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = RSAAlgorithm.from_jwk(key)
                self._rsa_key_cache[kid] = rsa_key
                return rsa_key

        return None

    async def authenticate_token(self, oauth_token: str, request: Request | None = None) -> UserIdentity:
        """
        Authenticates a user using an OAuth2 token string.
        """
        try:
            unverified_header = jwt.get_unverified_header(oauth_token)
            kid = unverified_header.get("kid")

            if not kid:
                logger.warning("Token missing kid in header")
                raise HTTPException(status_code=401, detail="Invalid token format")

            rsa_key = await self._get_rsa_key(kid)

            if not rsa_key:
                logger.warning("No matching key found for kid: %s", kid)
                raise HTTPException(status_code=401, detail="Token verification failed")

            decoded_token = jwt.decode(
                oauth_token,
                rsa_key,
                algorithms=["RS256"],
                audience=OAuth2Settings().CLIENT_ID,
                issuer=f"{OAuth2Settings().AUTHORITY_URL}/v2.0",
            )

            oid = decoded_token.get("oid")
            name = decoded_token.get("name", "")
            email = decoded_token.get("preferred_username", "")

            if not oid:
                logger.warning("Token missing oid claim")
                raise HTTPException(status_code=401, detail="Invalid token claims")

            user_entity = UserEntity.ensure_user_exists_for_auth(
                oid=oid,
                name=name,
                email=email,
            )

            # Resolve tenant context from request or use default
            if request:
                tenant = self.resolve_tenant_for_user(request, user_entity.id)
            else:
                # Fallback for contexts without request (e.g., WebSocket)
                tenant = self.get_default_tenant_for_user(user_entity.id)

            return UserIdentity.from_user_entity(user_entity, tenant)

        except jwt.ExpiredSignatureError:
            logger.info("Token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token: %s", str(e))
            raise HTTPException(status_code=401, detail="Token verification failed: Invalid token")
        except HTTPException:
            # Re-raise HTTPExceptions as-is (e.g., from tenant resolution)
            raise
        except httpx.HTTPError:
            logger.exception("HTTP error during token validation")
            raise HTTPException(status_code=500, detail="Authentication service unavailable")
        except Exception as e:
            logger.exception("Unexpected error during token validation: %s", str(e))
            raise HTTPException(status_code=500, detail="Authentication error")
