import logging

import httpx
import jwt
from cachetools import TTLCache
from fastapi import HTTPException, Security
from jwt.algorithms import RSAAlgorithm
from pydantic import ValidationError

from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Settings import OAuth2Settings
from aihub_lib.auth.identity.AzureIdentityProvider.AzureGraphService import AzureGraphService
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.user.UserEntity import UserEntity

logger = logging.getLogger(__name__)


class OAuth2AuthHandler:
    """
    A FastAPI dependency for OAuth2 authentication via Azure AD.

    Validates JWT tokens using JWKS from Microsoft Identity Platform, then fetches
    user profile from Azure Graph and ensures the user exists locally.
    """

    _jwks_cache: TTLCache = TTLCache(maxsize=100, ttl=21600)
    _rsa_key_cache: TTLCache = TTLCache(maxsize=10, ttl=21600)

    def __init__(self):
        self.config = OAuth2Settings()
        self.graph_service = AzureGraphService(self.config.CLIENT_ID)

    async def __call__(self, oauth_token: str = Security(OAuth2Settings().SCHEMA)) -> UserIdentity:
        return await self.authenticate_token(oauth_token)

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

    async def authenticate_token(self, oauth_token: str) -> UserIdentity:
        """Authenticates a user using an OAuth2 token string."""
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

            try:
                oid = decoded_token.get("oid")
                return await self._get_user_identity(oid)
            except ValidationError:
                logger.exception("Token validation error")
                raise HTTPException(status_code=422, detail="Invalid token claims")

        except jwt.ExpiredSignatureError:
            logger.info("Token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token: %s", str(e))
            raise HTTPException(status_code=401, detail="Token verification failed: Invalid token")
        except httpx.HTTPError:
            logger.exception("HTTP error during token validation")
            raise HTTPException(status_code=500, detail="Authentication service unavailable")
        except ValueError as e:
            logger.exception("Unexpected error during token validation: %s", str(e))
            raise HTTPException(status_code=500, detail="User identity error")
        except Exception as e:
            logger.exception("Unexpected error during token validation: %s", str(e))
            raise HTTPException(status_code=500, detail="Authentication error")

    async def _get_user_identity(self, oid: str) -> UserIdentity:
        """Fetches user profile from Azure Graph and ensures user exists locally."""
        graph_identity = await self.graph_service.get_user_identity_by_oid(oid)

        user_entity = UserEntity.ensure_user_exists_for_auth(
            oid=graph_identity.id,
            name=graph_identity.name,
            email=graph_identity.email,
            profile_image=graph_identity.profile_image,
        )

        return UserIdentity(
            id=user_entity.id,
            name=user_entity.name,
            email=user_entity.email,
            roles=user_entity.roles,
            profile_image=user_entity.profile_image,
        )

    async def get_user_identity_by_email(self, email: str) -> UserIdentity:
        """Fetches user identity by email from Azure Graph."""
        graph_identity = await self.graph_service.get_user_identity_by_email(email)
        return await self._get_user_identity(graph_identity.id)
