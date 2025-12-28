"""Keycloak identity provider settings."""

from typing import Annotated

from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import Field, computed_field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class KeycloakSettings(EnvironmentSettings):
    """
    Configuration settings for Keycloak OIDC integration.

    Loads configuration from environment variables with KEYCLOAK_ prefix.
    Provides computed properties for constructing OIDC endpoints.
    """

    model_config = EnvironmentSettings.create_settings_config("KEYCLOAK_")

    URL: Annotated[str, Field(description="Keycloak base URL (e.g., http://localhost:8180)")]
    REALM: Annotated[str, Field(description="Keycloak realm name")] = "aihub"

    @computed_field
    @property
    def ISSUER_URL(self) -> str:
        """OIDC issuer URL for the realm."""
        return f"{self.URL}/realms/{self.REALM}"

    @computed_field
    @property
    def JWKS_URL(self) -> str:
        """JWKS endpoint for obtaining public keys used to sign tokens."""
        return f"{self.ISSUER_URL}/protocol/openid-connect/certs"

    @computed_field
    @property
    def TOKEN_URL(self) -> str:
        """Token endpoint for OAuth2 token retrieval."""
        return f"{self.ISSUER_URL}/protocol/openid-connect/token"

    @computed_field
    @property
    def AUTHORIZATION_URL(self) -> str:
        """Authorization endpoint for OAuth2 authorization code flow."""
        return f"{self.ISSUER_URL}/protocol/openid-connect/auth"

    @computed_field
    @property
    def USERINFO_URL(self) -> str:
        """Userinfo endpoint for retrieving user claims."""
        return f"{self.ISSUER_URL}/protocol/openid-connect/userinfo"

    @computed_field
    @property
    def WELL_KNOWN_URL(self) -> str:
        """OpenID Connect discovery URL."""
        return f"{self.ISSUER_URL}/.well-known/openid-configuration"

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
