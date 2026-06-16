import logging
from typing import Annotated, Self

from fastapi import Depends, Security
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.routes import TenantScopedController

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.routes.access.access_capability_service import AccessCapabilityService
from swiss_ai_hub.api.routes.access.access_preset_service import AccessPresetService
from swiss_ai_hub.api.routes.access.dto.access_capabilities_dto import AccessCapabilitiesResponse
from swiss_ai_hub.api.routes.access.dto.access_capabilities_request import AccessCapabilitiesRequest
from swiss_ai_hub.api.routes.access.dto.access_preset_dto import AccessPresetDTO

logger = logging.getLogger(__name__)


class AccessController(TenantScopedController):
    """Serves the access-capability catalog and preset library used by the role / tenant-ceiling editors.

    The catalog is built **locally** from the controllers this runner actually serves. A curated plane
    (sysadmin-api) that mounts only a subset of the platform overrides these endpoints to proxy them to
    the main platform API instead — see ``SysadminAccessController``.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.access.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.access.description")
    icon = "mage:key"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/access", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_access_capabilities(self, route: str = "/capabilities") -> Self:
        @self.router.post(
            route,
            summary="Evaluate Access Capabilities",
            description="Returns the catalog of concrete capabilities (per service, agent and process), each with "
            "its exact access rule and whether the supplied draft rules grant it.",
            tags=self.tags,
        )
        async def get_access_capabilities(
            request: AccessCapabilitiesRequest,
            user: Annotated[
                UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> AccessCapabilitiesResponse:
            # `is_sys_admin` and `restrict_to_tenant` come from the request body, so without this gate a
            # non-sysadmin role admin could claim sysadmin or drop the ceiling to enumerate every agent,
            # process and knowledge namespace platform-wide. Both privileges require the *acting* user to
            # actually be a sysadmin; everyone else is forced to a ceiling-bounded, non-sysadmin view.
            acting_is_sys_admin = user.is_sys_admin
            subject = AccessChecker(
                user_access_rules=request.access_rules,
                tenant_access_rules=request.access_rules,
                is_sys_admin=request.is_sys_admin and acting_is_sys_admin,
            )
            ceiling = None
            if request.restrict_to_tenant or not acting_is_sys_admin:
                tenant_rules = user.acting_within_tenant.access_rules
                ceiling = AccessChecker(user_access_rules=tenant_rules, tenant_access_rules=tenant_rules)
            return await AccessCapabilityService.build_capabilities(subject, self._runner, t, ceiling)

        return self

    def get_access_presets(self, route: str = "/presets") -> Self:
        @self.router.get(
            route,
            summary="List Access Presets",
            description="Returns a curated, described library of common access rules for one-click authoring.",
            tags=self.tags,
        )
        async def get_access_presets(
            _: Annotated[UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[AccessPresetDTO]:
            return AccessPresetService.get_presets(t)

        return self
