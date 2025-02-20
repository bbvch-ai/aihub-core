from datetime import datetime, timezone
from typing import List

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.records.User import User
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, HTTPException, status, Security

from aihub_api.routes.token.dto.CreateTokenRequest import CreateTokenRequest
from aihub_api.routes.token.dto.CreateTokenResponse import CreateTokenResponse
from aihub_api.routes.token.dto.RevokeTokenResponse import RevokeTokenResponse
from aihub_api.routes.token.dto.TokenResponse import TokenResponse
from aihub_api.routes.token.TokenService import TokenService


class TokenController(Controller):
    def __init__(self, route: str = "/tokens", auth: AuthHandler | None = None):
        super().__init__(route, auth)

    def create_token(self, route: str = "/") -> "TokenController":
        @self.router.post(
            route,
            summary="Create API Token",
            description="Creates a new API token.",
            status_code=status.HTTP_201_CREATED,
        )
        async def create_token_endpoint(
            token_data: CreateTokenRequest, user: AuthenticatedUser = Security(self.auth)
        ) -> CreateTokenResponse:
            try:
                return TokenService.create_token(
                    name=token_data.name,
                    expiry_date=token_data.expiry_date,
                    user=user,
                    roles=token_data.roles,
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        return self

    def list_tokens(self, route: str = "/") -> "TokenController":
        @self.router.get(
            route,
            summary="List API Tokens",
            description="Lists all API tokens for the authenticated user. The token value is not returned.",
        )
        async def list_tokens_endpoint(user: User = Security(self.auth)) -> List[TokenResponse]:
            return TokenService.list_tokens(user)

        return self

    def revoke_token(self, route: str = "/{token_id}") -> "TokenController":
        @self.router.delete(
            route,
            summary="Revoke API Token",
            description="Revokes (deletes) an API token for the authenticated user.",
        )
        async def revoke_token_endpoint(token_id: str, user: User = Security(self.auth)) -> RevokeTokenResponse:
            try:
                TokenService.revoke_token(token_id, user)
                return RevokeTokenResponse(detail="Token revoked successfully.")
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        return self
