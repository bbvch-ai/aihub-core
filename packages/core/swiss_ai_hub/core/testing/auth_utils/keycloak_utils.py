from keycloak import KeycloakAdmin

from swiss_ai_hub.core.auth.keycloak.keycloak_settings import KeycloakSettings


def create_real_keycloak_admin() -> KeycloakAdmin:
    """Creates a KeycloakAdmin client configured from environment settings."""
    settings = KeycloakSettings()
    return KeycloakAdmin(
        server_url=settings.URL,
        realm_name=settings.REALM,
        client_id=settings.API_SERVICE_CLIENT_ID,
        client_secret_key=settings.API_SERVICE_CLIENT_SECRET,
    )
