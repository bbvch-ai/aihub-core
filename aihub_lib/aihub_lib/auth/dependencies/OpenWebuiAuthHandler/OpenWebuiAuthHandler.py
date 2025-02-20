import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.BearerAuthHandler import BearerAuthHandler
from aihub_lib.persistence.access.entities.BearerToken import BearerToken

logger = logging.getLogger(__name__)


class OpenWebuiAuthHandler(BearerAuthHandler):
    """
    A FastAPI dependency that implements authentication for the open-webui frontend.

    This dependency expects the following headers to be present in the incoming request:
        - "X-OpenWebUI-User-Name": The user's full name.
        - "X-OpenWebUI-User-Id": The user's unique identifier.
        - "X-OpenWebUI-User-Email": The user's email address.
        - "X-OpenWebUI-User-Role": The user's role.

    The dependency extracts user information from these headers and maps it onto an `AuthenticatedUser`
    instance. If any of the required headers are missing or empty, an `HTTPException` with a 401 Unauthorized
    status is raised.

    Note:
        This authentication handler is intended for use exclusively with open-webui as the frontend.
    """

    async def __call__(self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())) -> AuthenticatedUser:
        user_name = request.headers.get("X-OpenWebUI-User-Name")
        user_email = request.headers.get("X-OpenWebUI-User-Email")

        token_str = bearer_token.credentials
        if not token_str:
            raise HTTPException(status_code=401, detail="Token missing.")

        try:
            access_token = BearerToken.verify_token(token_str)
        except ValueError as e:
            logger.warning("Token authentication failed: %s", e)
            raise HTTPException(status_code=401, detail=str(e))

        return AuthenticatedUser(
            name=user_name or access_token.user.name,
            preferred_username=user_email or access_token.user.preferred_username,
            oid=access_token.user.oid,
            roles=access_token.roles,
        )
