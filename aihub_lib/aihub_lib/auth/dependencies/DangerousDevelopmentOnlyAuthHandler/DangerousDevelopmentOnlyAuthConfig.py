from typing import List, Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode


class DangerousDevelopmentOnlyAuthConfig(BaseSettings):
    """
    Configuration for the no-auth scenario, which provides a static user profile
    without requiring any actual authentication.

    ### Why This Config?
    In development or testing environments, you might not have a fully configured
    authentication system. `DangerousDevelopmentOnlyAuthConfig` allows you to proceed without authentication
    by supplying a fake user identity, ensuring your code can run and be tested even
    before the authentication integration is complete.
    """

    NAME: str = Field("Melanie Musterfrau", description="The user's displayed name.")
    EMAIL: str = Field(
        "melanie.musterfrau@bbv.ch",
        description="The user's email (often used as a login or unique identifier).",
    )
    OID: str = Field(
        "e07b0ebf-fd9f-485a-aa17-c1385d202f5b",
        description="A unique OID (Object ID) for the user. Defaults to a UUID.",
    )
    ROLES: Annotated[List[str], NoDecode] = Field("AllAgents", description="A list of roles this user possesses.")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator('ROLES', mode='before')
    @classmethod
    def decode_roles(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, list):
            return v
        return v.split(',')
