import json

from keycloak import KeycloakAdmin
from redis.asyncio import Redis
from swiss_ai_hub.core.auth import KeycloakSettings
from swiss_ai_hub.core.infrastructure import trace_fn

from swiss_ai_hub.api.routes.auth_provider.dto.auth_provider_response import AuthProviderResponse
from swiss_ai_hub.api.routes.auth_provider.dto.tenant_auth_provider_response import TenantAuthProviderResponse

DEFAULT_ICON = "pi-sign-in"
CACHE_KEY = "auth_providers"
LOGIN_ALIASES_CACHE_KEY = "auth_providers:login_aliases"
CACHE_TTL_SECONDS = 300


class AuthProviderService:
    """
    Retrieves available identity providers from Keycloak Admin API.
    Results are cached in Redis to keep the API stateless.
    """

    @staticmethod
    @trace_fn
    async def get_auth_providers(redis: Redis) -> list[AuthProviderResponse]:
        cached = await redis.get(CACHE_KEY)
        if cached:
            return [AuthProviderResponse.model_validate(item) for item in json.loads(cached)]

        keycloak_settings = KeycloakSettings()
        idps = await AuthProviderService._fetch_idps(keycloak_settings)
        providers = AuthProviderService._filter_providers(idps)

        if keycloak_settings.SHOW_KEYCLOAK_LOGIN:
            providers.append(
                AuthProviderResponse(
                    alias="",
                    display_name="Keycloak",
                    icon="pi-lock",
                )
            )

        await redis.set(CACHE_KEY, json.dumps([p.model_dump() for p in providers]), ex=CACHE_TTL_SECONDS)
        return providers

    @staticmethod
    @trace_fn
    async def get_tenant_auth_provider(redis: Redis, tenant_id: str) -> TenantAuthProviderResponse:
        """Consults only the configured mapping, never tenant existence, so unknown and unlisted tenants look alike."""
        alias = KeycloakSettings().TENANT_IDP_ALIASES.get(tenant_id)
        if alias is None:
            return TenantAuthProviderResponse(alias=None)

        login_aliases = await AuthProviderService._get_login_aliases(redis)
        return TenantAuthProviderResponse(alias=alias if alias in login_aliases else None)

    @staticmethod
    async def _get_login_aliases(redis: Redis) -> set[str]:
        cached = await redis.get(LOGIN_ALIASES_CACHE_KEY)
        if cached:
            return set(json.loads(cached))

        idps = await AuthProviderService._fetch_idps(KeycloakSettings())
        aliases = AuthProviderService._filter_login_aliases(idps)
        await redis.set(LOGIN_ALIASES_CACHE_KEY, json.dumps(sorted(aliases)), ex=CACHE_TTL_SECONDS)
        return aliases

    @staticmethod
    async def _fetch_idps(keycloak_settings: KeycloakSettings) -> list[dict]:
        admin = KeycloakAdmin(
            server_url=keycloak_settings.URL,
            realm_name=keycloak_settings.REALM,
            client_id=keycloak_settings.API_SERVICE_CLIENT_ID,
            client_secret_key=keycloak_settings.API_SERVICE_CLIENT_SECRET,
        )
        return await admin.a_get_idps()

    @staticmethod
    def _filter_login_aliases(idps: list[dict]) -> set[str]:
        """Hidden providers stay usable: Keycloak still honours kc_idp_hint for them, and that is all a link sends."""
        return {idp["alias"] for idp in idps if idp.get("enabled", False) and not idp.get("linkOnly", False)}

    @staticmethod
    def _filter_providers(idps: list[dict]) -> list[AuthProviderResponse]:
        providers: list[AuthProviderResponse] = []
        for idp in idps:
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
