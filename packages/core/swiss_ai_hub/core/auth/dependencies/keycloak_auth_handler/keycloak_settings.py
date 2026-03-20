from typing import Annotated

from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import Field, computed_field, field_validator

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class KeycloakSettings(EnvironmentSettings):
    """
    Configuration settings for Keycloak OIDC integration.

    Loads configuration from environment variables with KEYCLOAK_ prefix.
    Provides computed properties for constructing OIDC endpoints.
    """

    model_config = EnvironmentSettings.create_settings_config("KEYCLOAK_")

    URL: Annotated[str, Field(description="Keycloak internal URL for direct access (e.g., http://keycloak:8080)")]
    EXTERNAL_URL: Annotated[
        str | None, Field(description="Keycloak external URL as seen by browsers, used for issuer validation")
    ] = None
    REALM: Annotated[str, Field(description="Keycloak realm name")] = "aihub"
    API_SERVICE_CLIENT_ID: Annotated[str, Field(description="Client ID for the API service account")] = (
        "aihub-api-service"
    )
    API_SERVICE_CLIENT_SECRET: Annotated[str | None, Field(description="Client secret for the API service account")] = (
        None
    )
    SHOW_KEYCLOAK_LOGIN: Annotated[
        bool, Field(description="Show a direct Keycloak login button alongside federated IDPs")
    ] = True

    @field_validator("API_SERVICE_CLIENT_SECRET", mode="before")
    @classmethod
    def _empty_secret_is_none(cls, v: object) -> object:
        if v == "":
            return None
        return v

    @field_validator("SHOW_KEYCLOAK_LOGIN", mode="before")
    @classmethod
    def _empty_string_defaults_to_true(cls, v: object) -> object:
        if v == "":
            return True
        return v

    @computed_field
    @property
    def ISSUER_URL(self) -> str:
        """OIDC issuer URL matching the token's iss claim (uses external URL)."""
        base = self.EXTERNAL_URL or self.URL
        return f"{base}/realms/{self.REALM}"

    @computed_field
    @property
    def JWKS_URL(self) -> str:
        """JWKS endpoint — uses internal URL for direct network access."""
        return f"{self.URL}/realms/{self.REALM}/protocol/openid-connect/certs"

    @computed_field
    @property
    def TOKEN_URL(self) -> str:
        """Token endpoint for OAuth2 token retrieval."""
        return f"{self.URL}/realms/{self.REALM}/protocol/openid-connect/token"

    @computed_field
    @property
    def AUTHORIZATION_URL(self) -> str:
        """Authorization endpoint for OAuth2 authorization code flow (external, browser-facing)."""
        base = self.EXTERNAL_URL or self.URL
        return f"{base}/realms/{self.REALM}/protocol/openid-connect/auth"

    @computed_field
    @property
    def USERINFO_URL(self) -> str:
        """Userinfo endpoint for retrieving user claims."""
        return f"{self.URL}/realms/{self.REALM}/protocol/openid-connect/userinfo"

    @computed_field
    @property
    def WELL_KNOWN_URL(self) -> str:
        """OpenID Connect discovery URL."""
        return f"{self.URL}/realms/{self.REALM}/.well-known/openid-configuration"

    @computed_field
    @property
    def IDENTITY_PROVIDER_URL(self) -> str:
        """Admin API endpoint for listing identity providers in the configured realm."""
        return f"{self.URL}/admin/realms/{self.REALM}/identity-provider/instances"

    @computed_field
    @property
    def SCHEMA(self) -> OAuth2AuthorizationCodeBearer:
        """
        OAuth2AuthorizationCodeBearer schema configured for Keycloak.
        Used as a FastAPI dependency to handle the OAuth2 code flow.
        """
        return OAuth2AuthorizationCodeBearer(
            authorizationUrl=self.AUTHORIZATION_URL,
            tokenUrl=self.TOKEN_URL,
            scopes={"openid": "OpenID Connect", "email": "Email", "profile": "Profile"},
        )

    @computed_field
    @property
    def OPTIONAL_SCHEMA(self) -> OAuth2AuthorizationCodeBearer:
        """
        OAuth2AuthorizationCodeBearer schema that doesn't raise errors.
        Use when other auth methods are also provided.
        """
        return OAuth2AuthorizationCodeBearer(
            authorizationUrl=self.AUTHORIZATION_URL,
            tokenUrl=self.TOKEN_URL,
            scopes={"openid": "OpenID Connect", "email": "Email", "profile": "Profile"},
            auto_error=False,
        )
