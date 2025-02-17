import logging

from fastapi import HTTPException, Request

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.persistence.access.entities.AccessToken import AccessToken

logger = logging.getLogger(__name__)


class TokenAuthHandler(AuthHandler):
    """
    A FastAPI dependency that implements token-based authentication.

    This dependency expects a Bearer token in the `Authorization` header of the incoming request.
    It performs the following steps:
      1. Extracts the token from the header.
      2. Validates the token by performing a database lookup via `AccessToken.verify_token`.
      3. Checks that the token is correctly formatted, exists in the database, and is not expired.
      4. Maps the token's stored API user data onto an `AuthenticatedUser` instance.

    If any of these checks fail (e.g., if the token is missing, malformed, not found, or expired),
    an `HTTPException` with a 401 Unauthorized status is raised.

    Returns:
        AuthenticatedUser: A user instance constructed from the token's associated API user details.
    """

    async def __call__(self, request: Request) -> AuthenticatedUser:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header format.")

        token_str = auth_header[len("Bearer ") :].strip()

        try:
            # This call should perform a DB lookup and verify the token.
            access_token = AccessToken.verify_token(token_str)
        except ValueError as e:
            logger.warning("Token authentication failed: %s", e)
            raise HTTPException(status_code=401, detail=str(e))

        # Map the token's stored API user onto an AuthenticatedUser.
        api_user = access_token.user
        return AuthenticatedUser(
            name=api_user.name,
            preferred_username=api_user.preferred_username,
            oid=str(access_token.id),
            roles=access_token.roles,
        )
