import jwt
from fastapi import Depends, HTTPException
import httpx
from jwt.algorithms import RSAAlgorithm

from pydantic import ValidationError

from api_core.auth.AuthenticatedUser import AuthenticatedUser
from api_core.auth.dependencies.oauth2.OAuth2Config import OAuth2Config


async def use_oauth2_user(token: str = Depends(OAuth2Config().SCHEMA)) -> AuthenticatedUser:
    try:
        async with httpx.AsyncClient() as client:
            jwks_response = await client.get(OAuth2Config().JWKS_URL)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()

        unverified_header = jwt.get_unverified_header(token)
        rsa_key = None

        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = RSAAlgorithm.from_jwk(key)
                break

        if not rsa_key:
            raise HTTPException(status_code=401, detail="Token key ID not found")

        decoded_token = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=OAuth2Config().CLIENT_ID,
            issuer=f"{OAuth2Config().AUTHORITY}/v2.0"
        )

        try:
            # Parse the decoded token into the User Pydantic model
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
