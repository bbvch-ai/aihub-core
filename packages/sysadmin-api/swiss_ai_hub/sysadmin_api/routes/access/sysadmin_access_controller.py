import logging
from typing import Annotated, Self

from fastapi import Body, HTTPException, Request, Security, status
from swiss_ai_hub.api import AccessCapabilitiesRequest, AccessCapabilitiesResponse, AccessController, AccessPresetDTO
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity

from swiss_ai_hub.sysadmin_api.routes.access.platform_access_proxy import PlatformAccessProxy

logger = logging.getLogger(__name__)


class SysadminAccessController(AccessController):
    """The sysadmin plane's AccessController.

    The sysadmin plane mounts only a curated subset of the platform, so it cannot build the access
    catalog locally — the catalog depends on the full set of controllers a deployment serves. This
    subclass therefore **overrides** the catalog endpoints to proxy them server-to-server to the main
    platform API, preserving the exact request/response contract its parent declares.
    """

    def get_access_capabilities(self, route: str = "/capabilities") -> Self:
        @self.router.post(
            route,
            summary="Evaluate Access Capabilities",
            description="Returns the catalog of concrete capabilities (per service, agent and process), each with "
            "its exact access rule and whether the supplied draft rules grant it.",
            tags=self.tags,
        )
        async def get_access_capabilities(
            request: Annotated[AccessCapabilitiesRequest, Body()],
            http_request: Request,
            _: Annotated[UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))],
        ) -> AccessCapabilitiesResponse:
            return await PlatformAccessProxy.fetch_capabilities(
                self._platform_api_base_url(), http_request.path_params["tenant_id"], http_request, request
            )

        return self

    def get_access_presets(self, route: str = "/presets") -> Self:
        @self.router.get(
            route,
            summary="List Access Presets",
            description="Returns a curated, described library of common access rules for one-click authoring.",
            tags=self.tags,
        )
        async def get_access_presets(
            http_request: Request,
            _: Annotated[UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))],
        ) -> list[AccessPresetDTO]:
            return await PlatformAccessProxy.fetch_presets(
                self._platform_api_base_url(), http_request.path_params["tenant_id"], http_request
            )

        return self

    def _platform_api_base_url(self) -> str:
        base_url = self._runner.platform_api_base_url
        if base_url is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Sysadmin plane has no platform API base URL configured to proxy the access catalog to.",
            )
        return base_url
