from typing import Annotated, Self

from fastapi import Security
from swiss_ai_hub.core.auth import AuthHandler, UserIdentity
from swiss_ai_hub.core.routes import TenantScopedController

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.tenant_settings.dto.tenant_settings_dto import TenantSettingsDTO
from swiss_ai_hub.api.routes.tenant_settings.tenant_settings_service import TenantSettingsService


class TenantSettingsController(TenantScopedController):
    name = ApiLocaleString.from_i18n_path("api.controllers.tenant_settings.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.tenant_settings.description")
    icon = "mage:settings"

    def __init__(self, *, auth: AuthHandler, route: str = "/tenant-settings") -> None:
        super().__init__(
            auth=auth,
            route=route,
            additionally_required_permission="aihub.admin.service.tenantsettings",
        )

    def get_tenant_settings(self, route: str = "") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_tenant_settings(
            user: Annotated[
                UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))
            ],
        ) -> TenantSettingsDTO:
            return await TenantSettingsService.get_settings(user.acting_within_tenant.id)

        return self

    def update_tenant_settings(self, route: str = "") -> Self:
        @self.router.put(route, tags=self.tags)
        async def update_tenant_settings(
            settings: TenantSettingsDTO,
            user: Annotated[
                UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))
            ],
        ) -> TenantSettingsDTO:
            return await TenantSettingsService.update_settings(user.acting_within_tenant.id, settings)

        return self
