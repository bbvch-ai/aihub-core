from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OAuth2Config(BaseSettings):
    TENANT_ID: str = Field(..., description="The tenant ID of the Azure AD tenant.")
    CLIENT_ID: str = Field(..., description="The client ID of the application.")
    AUTHORITY_URL: str = Field(..., description="The authority URL of the Azure AD tenant.")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @computed_field
    @property
    def AUTHORITY(self) -> str:
        return f"{self.AUTHORITY_URL}/{self.TENANT_ID}"

    @computed_field
    @property
    def TOKEN_URL(self) -> str:
        return f"{self.AUTHORITY}/oauth2/v2.0/token"

    @computed_field
    @property
    def JWKS_URL(self) -> str:
        return f"{self.AUTHORITY}/discovery/v2.0/keys"

    @computed_field
    @property
    def SCHEMA(self) -> OAuth2AuthorizationCodeBearer:
        return OAuth2AuthorizationCodeBearer(
            authorizationUrl=f"{self.AUTHORITY}/oauth2/v2.0/authorize",
            tokenUrl=self.TOKEN_URL,
            scopes={"User.Read": "Read user profile data"},
        )