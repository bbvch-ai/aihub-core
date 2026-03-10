import json

from keycloak import KeycloakAdmin
from redis.asyncio import Redis
from swiss_ai_hub.core.auth.dependencies.KeycloakAuthHandler.KeycloakSettings import KeycloakSettings
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

from swiss_ai_hub.api.routes.auth_provider.dto.AuthProviderResponse import AuthProviderResponse

DEFAULT_ICON = "pi-sign-in"
CACHE_KEY = "auth_providers"
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

        admin = KeycloakAdmin(
            server_url=keycloak_settings.URL,
            realm_name=keycloak_settings.REALM,
            client_id=keycloak_settings.API_SERVICE_CLIENT_ID,
            client_secret_key=keycloak_settings.API_SERVICE_CLIENT_SECRET,
        )
        idps = await admin.a_get_idps()
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
