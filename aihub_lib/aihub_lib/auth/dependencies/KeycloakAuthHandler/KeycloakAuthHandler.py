"""Keycloak OIDC authentication handler."""

import logging
from typing import Any

import httpx
import jwt
from cachetools import TTLCache
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from fastapi import HTTPException, Security
from jwt.algorithms import RSAAlgorithm

from aihub_lib.auth.dependencies.KeycloakAuthHandler.KeycloakSettings import KeycloakSettings
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.user.UserEntity import UserEntity

logger = logging.getLogger(__name__)


class KeycloakAuthHandler:
    """
    A FastAPI dependency for Keycloak OIDC authentication.

    Validates JWT tokens using JWKS from Keycloak. User data is extracted
    directly from JWT claims - no external API calls needed after JWKS fetch.
    """

    _jwks_cache: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=100, ttl=21600)  # 6 hour cache
    _rsa_key_cache: TTLCache[str, RSAPublicKey | RSAPrivateKey] = TTLCache(maxsize=10, ttl=21600)

    def __init__(self) -> None:
        self.config = KeycloakSettings()

    async def __call__(self, oauth_token: str = Security(KeycloakSettings().SCHEMA)) -> UserIdentity:
        return await self.authenticate_token(oauth_token)

    async def _get_jwks(self) -> dict[str, Any]:
        """Retrieves the JWKS from Keycloak, using caching to minimize API calls."""
        cache_key = "jwks"
        if cache_key in self._jwks_cache:
            return self._jwks_cache[cache_key]

        try:
            logger.debug("JWKS cache miss, fetching from %s", self.config.JWKS_URL)
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=30.0, read=10.0)) as client:
                jwks_response = await client.get(self.config.JWKS_URL)
                jwks_response.raise_for_status()
                jwks = jwks_response.json()
                self._jwks_cache[cache_key] = jwks
                return jwks
        except httpx.HTTPError as e:
            logger.exception("Error fetching JWKS: %s", str(e))
            raise HTTPException(status_code=500, detail="Authentication service unavailable")

    async def _get_rsa_key(self, kid: str) -> RSAPublicKey | RSAPrivateKey | None:
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
        """Authenticates a user using a Keycloak JWT token."""
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

            # Keycloak tokens use 'sub' as unique user identifier
            # The audience is typically 'account' for Keycloak tokens
            decoded_token = jwt.decode(
                oauth_token,
                rsa_key,
                algorithms=["RS256"],
                audience="account",
                issuer=self.config.ISSUER_URL,
                options={"verify_aud": False},  # Keycloak audience can vary by client
            )

            # Extract user info from Keycloak token claims
            sub = decoded_token.get("sub")
            name = decoded_token.get("name", decoded_token.get("preferred_username", ""))
            email = decoded_token.get("email", "")

            if not sub:
                logger.warning("Token missing sub claim")
                raise HTTPException(status_code=401, detail="Invalid token claims")

            user_entity = UserEntity.ensure_user_exists_for_auth(
                oid=sub,
                name=name,
                email=email,
            )

            return UserIdentity.from_user_entity(user_entity)

        except jwt.ExpiredSignatureError:
            logger.info("Token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token: %s", str(e))
            raise HTTPException(status_code=401, detail="Token verification failed: Invalid token")
        except httpx.HTTPError:
            logger.exception("HTTP error during token validation")
            raise HTTPException(status_code=500, detail="Authentication service unavailable")
        except Exception as e:
            logger.exception("Unexpected error during token validation: %s", str(e))
            raise HTTPException(status_code=500, detail="Authentication error")
