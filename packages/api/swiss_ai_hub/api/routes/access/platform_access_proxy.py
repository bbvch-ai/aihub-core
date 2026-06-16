import httpx
from fastapi import HTTPException, Request, status

from swiss_ai_hub.api.routes.access.dto.access_capabilities_dto import AccessCapabilitiesResponse
from swiss_ai_hub.api.routes.access.dto.access_capabilities_request import AccessCapabilitiesRequest
from swiss_ai_hub.api.routes.access.dto.access_preset_dto import AccessPresetDTO

_FORWARDED_HEADERS = ("authorization", "lang", "locale", "accept-language")
# Bound the server-to-server hop so a slow or hung main API surfaces as an error instead of
# blocking the sysadmin worker until the client gives up.
_TIMEOUT = httpx.Timeout(10.0)


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
        try:
            async with httpx.AsyncClient(base_url=base_url, timeout=_TIMEOUT) as client:
                response = await client.post(
                    f"/api/v1/{tenant_id}/roles/access/capabilities",
                    json=body.model_dump(),
                    headers=PlatformAccessProxy._forward_headers(request),
                )
                response.raise_for_status()
                return AccessCapabilitiesResponse.model_validate(response.json())
        except httpx.HTTPError as error:
            raise PlatformAccessProxy._gateway_error(error) from error

    @staticmethod
    async def fetch_presets(base_url: str, tenant_id: str, request: Request) -> list[AccessPresetDTO]:
        try:
            async with httpx.AsyncClient(base_url=base_url, timeout=_TIMEOUT) as client:
                response = await client.get(
                    f"/api/v1/{tenant_id}/roles/access/presets",
                    headers=PlatformAccessProxy._forward_headers(request),
                )
                response.raise_for_status()
                return [AccessPresetDTO.model_validate(item) for item in response.json()]
        except httpx.HTTPError as error:
            raise PlatformAccessProxy._gateway_error(error) from error

    @staticmethod
    def _gateway_error(error: httpx.HTTPError) -> HTTPException:
        """Translate a failed upstream call into a gateway-appropriate status instead of a generic 500:
        an upstream HTTP error passes its status through (so a forwarded 401/403 stays a 401/403), while
        a network or timeout failure becomes 502 — both far more debuggable for the sysadmin caller."""
        if isinstance(error, httpx.HTTPStatusError):
            return HTTPException(status_code=error.response.status_code, detail=error.response.text)
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach the platform API: {error}",
        )

    @staticmethod
    def _forward_headers(request: Request) -> dict[str, str]:
        return {name: value for name in _FORWARDED_HEADERS if (value := request.headers.get(name))}
