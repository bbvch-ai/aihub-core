import os
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
import httpx
from jwt.algorithms import RSAAlgorithm

from pydantic import ValidationError

from api_core.dto.User import User

TENANT_ID = os.getenv("AZURE_AD_TENANT_ID")
CLIENT_ID = os.getenv("AZURE_AD_CLIENT_ID")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
TOKEN_URL = f"{AUTHORITY}/oauth2/v2.0/token"
JWKS_URL = f"{AUTHORITY}/discovery/v2.0/keys"
SCOPES = ["User.Read"]

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{AUTHORITY}/oauth2/v2.0/authorize",
    tokenUrl=TOKEN_URL,
    scopes={"User.Read": "Read user profile data"},
)

async def user_from_token(token: str = Depends(oauth2_scheme)) -> User:
    try:
        async with httpx.AsyncClient() as client:
            jwks_response = await client.get(JWKS_URL)
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
            audience=CLIENT_ID,
            issuer=f"{AUTHORITY}/v2.0"
        )

        try:
            # Parse the decoded token into the User Pydantic model
            user = User(**decoded_token)
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
