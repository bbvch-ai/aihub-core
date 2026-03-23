from typing import Annotated, Self

from fastapi import Depends
from redis.asyncio import Redis
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.infrastructure import use_redis
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.auth_provider.auth_provider_service import AuthProviderService
from swiss_ai_hub.api.routes.auth_provider.dto.auth_provider_response import AuthProviderResponse


class AuthProviderController(Controller):
    name = ApiLocaleString.from_i18n_path("api.controllers.auth_provider.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.auth_provider.description")
    icon = "mage:shield-check"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/auth-providers", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_auth_providers(self, route: str = "/") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_auth_providers(redis: Annotated[Redis, Depends(use_redis)]) -> list[AuthProviderResponse]:
            return await AuthProviderService.get_auth_providers(redis)

        return self
