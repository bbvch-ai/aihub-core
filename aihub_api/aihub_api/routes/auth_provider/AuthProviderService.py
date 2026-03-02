"""Fetches available identity providers from the Keycloak Admin API using a least-privilege service account."""

import logging

import httpx
from aihub_lib.auth.dependencies.KeycloakAuthHandler.KeycloakSettings import KeycloakSettings
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from cachetools import TTLCache

from aihub_api.routes.auth_provider.dto.AuthProviderResponse import AuthProviderResponse

logger = logging.getLogger(__name__)

DEFAULT_ICON = "pi-sign-in"


class AuthProviderService:
    """Retrieves and caches identity providers from Keycloak Admin API."""

    _cache: TTLCache[str, list[AuthProviderResponse]] = TTLCache(maxsize=1, ttl=300)

    @staticmethod
    @trace_fn
    async def get_auth_providers() -> list[AuthProviderResponse]:
        """Fetches enabled, visible identity providers from Keycloak."""
        cache_key = "auth_providers"
        if cache_key in AuthProviderService._cache:
            return AuthProviderService._cache[cache_key]

        settings = KeycloakSettings()

        if not settings.API_SERVICE_CLIENT_SECRET:
            logger.warning("Keycloak API service account not configured, returning empty provider list")
            return AuthProviderService._build_fallback_list(settings)

        try:
            token = await AuthProviderService._get_service_account_token(settings)
            providers = await AuthProviderService._fetch_identity_providers(settings, token)

            if settings.SHOW_KEYCLOAK_LOGIN:
                providers.append(
                    AuthProviderResponse(
                        alias="",
                        display_name="Keycloak",
                        icon="pi-lock",
                    )
                )

            AuthProviderService._cache[cache_key] = providers
            return providers
        except Exception:
            logger.exception("Failed to fetch identity providers from Keycloak")
            return AuthProviderService._build_fallback_list(settings)

    @staticmethod
    async def _get_service_account_token(settings: KeycloakSettings) -> str:
        """Obtains a service account token via client_credentials grant."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.post(
                settings.TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.API_SERVICE_CLIENT_ID,
                    "client_secret": settings.API_SERVICE_CLIENT_SECRET,
                },
            )
            response.raise_for_status()
            return response.json()["access_token"]

    @staticmethod
    async def _fetch_identity_providers(settings: KeycloakSettings, token: str) -> list[AuthProviderResponse]:
        """Calls the Keycloak Admin API and filters to visible, enabled providers."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.get(
                settings.IDENTITY_PROVIDER_URL,
                headers={"Authorization": f"Bearer {token}"},
                params={"briefRepresentation": "true"},
            )
            response.raise_for_status()

        providers: list[AuthProviderResponse] = []
        for idp in response.json():
            if not idp.get("enabled", False):
                continue
            if idp.get("config", {}).get("hideOnLoginPage") == "true":
                continue
            if idp.get("linkOnly", False):
                continue

            alias = idp.get("alias", "")
            config = idp.get("config", {})

            providers.append(
                AuthProviderResponse(
                    alias=alias,
                    display_name=idp.get("displayName") or alias,
                    icon=config.get("icon", DEFAULT_ICON),
                )
            )

        return providers

    @staticmethod
    def _build_fallback_list(settings: KeycloakSettings) -> list[AuthProviderResponse]:
        """Returns a minimal fallback list when Keycloak Admin API is unavailable."""
        if settings.SHOW_KEYCLOAK_LOGIN:
            return [AuthProviderResponse(alias="", display_name="Keycloak", icon="pi-lock")]
        return []
