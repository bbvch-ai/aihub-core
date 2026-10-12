import json

from keycloak import KeycloakAdmin
from redis.asyncio import Redis
from swiss_ai_hub.core.auth import KeycloakSettings
from swiss_ai_hub.core.infrastructure import trace_fn

from swiss_ai_hub.api.routes.auth_provider.dto.auth_provider_response import AuthProviderResponse
from swiss_ai_hub.api.routes.auth_provider.dto.login_options_response import LoginOptionsResponse

DEFAULT_ICON = "pi-sign-in"
CACHE_KEY = "auth_providers"
LINKABLE_CACHE_KEY = "auth_providers:linkable"
CACHE_TTL_SECONDS = 300
KEYCLOAK_LOGIN_PROVIDER = AuthProviderResponse(alias="", display_name="Keycloak", icon="pi-lock")


class AuthProviderService:
    """
    Retrieves available identity providers from Keycloak Admin API.
    Results are cached in Redis to keep the API stateless.
    """

    @staticmethod
    @trace_fn
    async def get_login_options(redis: Redis) -> LoginOptionsResponse:
        """A welcome-page instance never fetches federated providers, so the anonymous answer cannot list tenants."""
        keycloak_settings = KeycloakSettings()
        if keycloak_settings.LOGIN_WELCOME_PAGE:
            providers = [KEYCLOAK_LOGIN_PROVIDER] if keycloak_settings.SHOW_KEYCLOAK_LOGIN else []
            return LoginOptionsResponse(welcome_page=True, providers=providers)

        return LoginOptionsResponse(welcome_page=False, providers=await AuthProviderService.get_auth_providers(redis))

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
            providers.append(KEYCLOAK_LOGIN_PROVIDER)

        await redis.set(CACHE_KEY, json.dumps([p.model_dump() for p in providers]), ex=CACHE_TTL_SECONDS)
        return providers

    @staticmethod
    @trace_fn
    async def get_auth_provider(redis: Redis, alias: str) -> AuthProviderResponse | None:
        """Resolves one provider for a per-tenant login link, so the link works without the full provider list."""
        linkable_providers = await AuthProviderService._get_linkable_providers(redis)
        return next((provider for provider in linkable_providers if provider.alias == alias), None)

    @staticmethod
    async def _get_linkable_providers(redis: Redis) -> list[AuthProviderResponse]:
        cached = await redis.get(LINKABLE_CACHE_KEY)
        if cached:
            return [AuthProviderResponse.model_validate(item) for item in json.loads(cached)]

        idps = await AuthProviderService._fetch_idps(KeycloakSettings())
        providers = AuthProviderService._filter_linkable_providers(idps)
        await redis.set(LINKABLE_CACHE_KEY, json.dumps([p.model_dump() for p in providers]), ex=CACHE_TTL_SECONDS)
        return providers

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
    def _filter_linkable_providers(idps: list[dict]) -> list[AuthProviderResponse]:
        """Hidden providers stay linkable: Keycloak still honours kc_idp_hint for them, and that is all a link sends."""
        return [
            AuthProviderService._to_response(idp)
            for idp in idps
            if idp.get("enabled", False) and not idp.get("linkOnly", False)
        ]

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

            providers.append(AuthProviderService._to_response(idp))

        return providers

    @staticmethod
    def _to_response(idp: dict) -> AuthProviderResponse:
        alias = idp.get("alias", "")
        return AuthProviderResponse(
            alias=alias,
            display_name=idp.get("displayName") or alias,
            icon=idp.get("config", {}).get("icon", DEFAULT_ICON),
        )
