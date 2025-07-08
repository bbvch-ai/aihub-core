from typing import Annotated

from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OAuth2Config(BaseSettings):
    """
    OAuth2 configuration settings for Azure AD integration.

    ### Why This Class?
    In order to authenticate users against Azure AD, we need a set of configuration parameters:
    - Tenant ID
    - Client ID
    - Authority (the Azure AD instance and tenant)
    - Token and JWKS URLs for retrieving signing keys and issuing tokens.

    `OAuth2Config`:
    - Loads these from environment variables or a `.env` file.
    - Provides computed properties to construct full URLs for authorization, token retrieval, and JWKS keys.
    - Returns an `OAuth2AuthorizationCodeBearer` schema, simplifying
      the integration with FastAPI's dependency injection.

    ### Example
    ```python
    config = OAuth2Config()
    print(config.TOKEN_URL)
    ```
    """

    TENANT_ID: Annotated[str, Field(description="The tenant ID of the Azure AD tenant.")]
    CLIENT_ID: Annotated[str, Field(description="The client ID of the application.")]
    AUTHORITY_URL: Annotated[str, Field(description="The authority URL of the Azure AD tenant.")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @computed_field
    @property
    def AUTHORITY(self) -> str:
        """Constructs the full Authority URL combining AUTHORITY_URL and TENANT_ID."""
        return f"{self.AUTHORITY_URL}/{self.TENANT_ID}"

    @computed_field
    @property
    def TOKEN_URL(self) -> str:
        """Provides the token endpoint for OAuth2 token retrieval."""
        return f"{self.AUTHORITY}/oauth2/v2.0/token"

    @computed_field
    @property
    def JWKS_URL(self) -> str:
        """Provides the JWKS endpoint for obtaining the public keys used to sign tokens."""
        return f"{self.AUTHORITY}/discovery/v2.0/keys"

    @computed_field
    @property
    def SCHEMA(self) -> OAuth2AuthorizationCodeBearer:
        """
        Returns an OAuth2AuthorizationCodeBearer schema configured for Azure AD.
        This is used as a FastAPI dependency to handle the OAuth2 code flow.
        """
        return OAuth2AuthorizationCodeBearer(
            authorizationUrl=f"{self.AUTHORITY}/oauth2/v2.0/authorize",
            tokenUrl=self.TOKEN_URL,
            scopes={"User.Read": "Read user profile data"},
        )

    @computed_field
    @property
    def OPTIONAL_SCHEMA(self) -> OAuth2AuthorizationCodeBearer:
        """
        Returns an OAuth2AuthorizationCodeBearer schema configured for Azure AD.
        Raises no error when not authenticated, only use in when other auth methods are provided as well
        """
        return OAuth2AuthorizationCodeBearer(
            authorizationUrl=f"{self.AUTHORITY}/oauth2/v2.0/authorize",
            tokenUrl=self.TOKEN_URL,
            scopes={"User.Read": "Read user profile data"},
            auto_error=False,
        )
