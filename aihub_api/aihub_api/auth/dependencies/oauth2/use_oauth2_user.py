from typing import Annotated

import httpx
import jwt
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from fastapi import Depends, HTTPException
from jwt.algorithms import RSAAlgorithm
from pydantic import ValidationError

from aihub_api.auth.dependencies.oauth2.OAuth2Config import OAuth2Config


async def use_oauth2_user(token: Annotated[str, Depends(OAuth2Config().SCHEMA)]) -> AuthenticatedUser:
    """
    A FastAPI dependency that:
    1. Validates the provided token using JWKS from Microsoft Identity Platform.
    2. Decodes and verifies the token signature and claims (audience, issuer).
    3. Constructs an `AuthenticatedUser` object from the token claims.

    ### Why This Dependency?
    In an OAuth2 secured application, incoming requests may carry a bearer token. `use_oauth2_user`:
    - Fetches JWKS keys to verify the token.
    - Checks if the token is valid and not expired.
    - Ensures the token's audience and issuer match what's expected from Azure AD.

    If the token fails any checks, it raises an HTTP 401 or 422 error.
    If successful, it returns an `AuthenticatedUser` representing the authenticated principal.

    ### Steps Involved
    1. Retrieve JWKS from Azure AD using `httpx`.
    2. Extract the token's header to find the key ID (kid).
    3. Match the kid to the corresponding JWKS key and construct an RSA key.
    4. Decode and verify the token with `jwt.decode`.
    5. Map claims onto `AuthenticatedUser`.

    ### Errors
    - 401 Unauthorized if the token is invalid, expired, or the key is not found.
    - 422 Unprocessable Entity if token claims cannot be parsed into `AuthenticatedUser`.
    """
    try:
        # Retrieve JWKS keys for signature verification
        async with httpx.AsyncClient() as client:
            jwks_response = await client.get(OAuth2Config().JWKS_URL)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()

        unverified_header = jwt.get_unverified_header(token)
        rsa_key = None

        # Find the matching key in JWKS
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = RSAAlgorithm.from_jwk(key)
                break

        if not rsa_key:
            raise HTTPException(status_code=401, detail="Token key ID not found")

        # Decode and verify JWT signature and claims
        decoded_token = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=OAuth2Config().CLIENT_ID,
            issuer=f"{OAuth2Config().AUTHORITY}/v2.0",
        )

        # Parse token claims into AuthenticatedUser
        try:
            user = AuthenticatedUser(**decoded_token)
        except ValidationError as ve:
            raise HTTPException(status_code=422, detail=f"Token validation error: {ve}")

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error during token validation: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating token: {str(e)}")
