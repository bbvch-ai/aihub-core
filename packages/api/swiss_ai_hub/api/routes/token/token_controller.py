from typing import Annotated, Self

from fastapi import HTTPException, Security, status
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.token.dto.create_token_request import CreateTokenRequest
from swiss_ai_hub.api.routes.token.dto.create_token_response import CreateTokenResponse
from swiss_ai_hub.api.routes.token.dto.revoke_token_response import RevokeTokenResponse
from swiss_ai_hub.api.routes.token.dto.token_response import TokenResponse
from swiss_ai_hub.api.routes.token.token_service import TokenService


class TokenController(Controller):
    name = ApiLocaleString.from_i18n_path("api.controllers.token.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.token.description")
    icon = "mage:key"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/tokens", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def create_token(self, route: str = "/") -> Self:
        @self.router.post(
            route,
            summary="Create API Token",
            description="Creates a new API token.",
            status_code=status.HTTP_201_CREATED,
            tags=self.tags,
        )
        async def create_token_endpoint(
            token_data: CreateTokenRequest,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> CreateTokenResponse:
            try:
                return TokenService.create_token(
                    name=token_data.name,
                    expiry_date=token_data.expiry_date,
                    user=user,
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        return self

    def list_tokens(self, route: str = "/") -> Self:
        @self.router.get(
            route,
            summary="List API Tokens",
            description="Lists all API tokens for the authenticated user. The token value is not returned.",
            tags=self.tags,
        )
        async def list_tokens_endpoint(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> list[TokenResponse]:
            return TokenService.list_tokens(user)

        return self

    def revoke_token(self, route: str = "/{token_id}") -> Self:
        @self.router.delete(
            route,
            summary="Revoke API Token",
            description="Revokes (deletes) an API token for the authenticated user.",
            tags=self.tags,
        )
        async def revoke_token_endpoint(
            token_id: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> RevokeTokenResponse:
            try:
                TokenService.revoke_token(token_id, user)
                return RevokeTokenResponse(detail="Token revoked successfully.")
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        return self
