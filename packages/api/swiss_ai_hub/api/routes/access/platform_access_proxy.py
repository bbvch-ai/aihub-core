import httpx
from fastapi import Request

from swiss_ai_hub.api.routes.access.dto.access_capabilities_dto import AccessCapabilitiesResponse
from swiss_ai_hub.api.routes.access.dto.access_capabilities_request import AccessCapabilitiesRequest
from swiss_ai_hub.api.routes.access.dto.access_preset_dto import AccessPresetDTO

_FORWARDED_HEADERS = ("authorization", "lang", "locale", "accept-language")


class PlatformAccessProxy:
    """Forwards access-catalog calls from a curated plane (sysadmin API) to the main platform API.

    The capability and preset catalogs depend on the controllers a deployment actually serves, which
    only the main API knows. A plane mounting a subset proxies the caller's request — bearer token and
    locale included — server-to-server, returning whatever the live platform API reports.
    """

    @staticmethod
    async def fetch_capabilities(
        base_url: str, tenant_id: str, request: Request, body: AccessCapabilitiesRequest
    ) -> AccessCapabilitiesResponse:
        async with httpx.AsyncClient(base_url=base_url) as client:
            response = await client.post(
                f"/api/v1/{tenant_id}/roles/access/capabilities",
                json=body.model_dump(),
                headers=PlatformAccessProxy._forward_headers(request),
            )
            response.raise_for_status()
            return AccessCapabilitiesResponse.model_validate(response.json())

    @staticmethod
    async def fetch_presets(base_url: str, tenant_id: str, request: Request) -> list[AccessPresetDTO]:
        async with httpx.AsyncClient(base_url=base_url) as client:
            response = await client.get(
                f"/api/v1/{tenant_id}/roles/access/presets",
                headers=PlatformAccessProxy._forward_headers(request),
            )
            response.raise_for_status()
            return [AccessPresetDTO.model_validate(item) for item in response.json()]

    @staticmethod
    def _forward_headers(request: Request) -> dict[str, str]:
        return {name: value for name in _FORWARDED_HEADERS if (value := request.headers.get(name))}
