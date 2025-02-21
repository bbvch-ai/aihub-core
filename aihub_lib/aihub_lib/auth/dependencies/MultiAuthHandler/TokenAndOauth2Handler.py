from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2AuthorizationCodeBearer

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.BearerAuthHandler import BearerAuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Config import OAuth2Config


class TokenAndOauth2Handler(AuthHandler):
    """A composite authentication handler that sequentially attempts both OAuth2 and Bearer auth strategies."""

    def __init__(self, bearer_handler: BearerAuthHandler, oauth2_handler: OAuth2AuthHandler):
        self.bearer_handler = bearer_handler
        self.oauth2_handler = oauth2_handler

    async def __call__(
            self,
            request: Request,
            bearer_token: HTTPAuthorizationCredentials | None = Security(HTTPBearer()),
            oauth_token: OAuth2AuthorizationCodeBearer | None = Security(OAuth2Config().SCHEMA),
    ) -> AuthenticatedUser:
        errors = []

        try:
            return await self.oauth2_handler(oauth_token)
        except HTTPException as exc:
            errors.append(f"OAuth2: {exc.detail}")
            if exc.status_code != 401:
                raise exc

        try:
            return await self.bearer_handler(request, bearer_token)
        except HTTPException as exc:
            errors.append(f"Bearer: {exc.detail}")
            if exc.status_code != 401:
                raise exc

        # If no strategy succeeded, raise an error with all failure details.
        raise HTTPException(status_code=401, detail=" | ".join(errors))
