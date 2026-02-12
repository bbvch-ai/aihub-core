import logging

import httpx
import jwt
from cachetools import TTLCache
from fastapi import HTTPException, Security
from jwt.algorithms import RSAAlgorithm
from pydantic import ValidationError

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Settings import OAuth2Settings
from aihub_lib.auth.identity.AzureIdentityProvider.AzureIdentityProvider import AzureIdentityProvider
from aihub_lib.auth.identity.UserIdentity import UserIdentity

logger = logging.getLogger(__name__)


class OAuth2AuthHandler(AuthHandler):
    """
    A FastAPI dependency that:
    1. Validates the provided token using JWKS from Microsoft Identity Platform.
    2. Decodes and verifies the token signature and claims (audience, issuer).
    3. Constructs an `UserIdentity` object from the token claims.

    ### Why This Dependency?
    In an OAuth2 secured application, incoming requests may carry a bearer token. `use_oauth2_user`:
    - Fetches JWKS keys to verify the token.
    - Checks if the token is valid and not expired.
    - Ensures the token's audience and issuer match what's expected from Azure AD.

    If the token fails any checks, it raises an HTTP 401 or 422 error.
    If successful, it returns an `UserIdentity` representing the authenticated principal.

    ### Steps Involved
    1. Retrieve JWKS from Azure AD using `httpx` (cached for performance).
    2. Extract the token's header to find the key ID (kid).
    3. Match the kid to the corresponding JWKS key and construct an RSA key.
    4. Decode and verify the token with `jwt.decode`.
    5. Map claims onto `UserIdentity`.

    ### Errors
    - 401 Unauthorized if the token is invalid, expired, or the key is not found.
    - 422 Unprocessable Entity if token claims cannot be parsed into `UserIdentity`.
    """

    _jwks_cache: TTLCache = TTLCache(maxsize=100, ttl=21600)
    _rsa_key_cache: TTLCache = TTLCache(maxsize=10, ttl=21600)

    def __init__(self, identity_provider: AzureIdentityProvider):
        super().__init__(identity_provider)
        self.config = OAuth2Settings()

    async def __call__(self, oauth_token: str = Security(OAuth2Settings().SCHEMA)) -> UserIdentity:
        return await self.authenticate_token(oauth_token)

    async def _get_jwks(self) -> dict:
        """
        Retrieves the JWKS from the configured URL, using caching to minimize API calls.
        """
        cache_key = "jwks"
        if cache_key in self._jwks_cache:
            return self._jwks_cache[cache_key]

        try:
            logger.debug("JWKS cache miss, fetching from %s", OAuth2Settings().JWKS_URL)
            # Increased connect timeout to 30s to allow IPv6 failures to fall back to IPv4
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
        """
        Gets an RSA key for the specified key ID (kid).
        Uses TTLCache to automatically manage key expiration.
        """
        if kid in self._rsa_key_cache:
            return self._rsa_key_cache[kid]

        # If not in cache, fetch fresh JWKS
        jwks = await self._get_jwks()

        # Find the matching key in JWKS
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = RSAAlgorithm.from_jwk(key)
                # Cache the key
                self._rsa_key_cache[kid] = rsa_key
                return rsa_key

        return None

    async def authenticate_token(self, oauth_token: str) -> UserIdentity:
        """
        Authenticates a user using an OAuth2 token string directly.
        Used for WebSocket authentication.
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

            # Decode and verify JWT signature and claims
            decoded_token = jwt.decode(
                oauth_token,
                rsa_key,
                algorithms=["RS256"],
                audience=OAuth2Settings().CLIENT_ID,
                issuer=f"{OAuth2Settings().AUTHORITY_URL}/v2.0",
            )

            try:
                oid = decoded_token.get("oid")
                return await self._identity_provider.get_user_identity_by_oid(oid)
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
            logger.exception("Unexpected error validating token")
            raise HTTPException(status_code=500, detail="Authentication error")
