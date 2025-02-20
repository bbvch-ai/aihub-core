import uuid
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NoAuthConfig(BaseSettings):
    """
    Configuration for the no-auth scenario, which provides a static user profile
    without requiring any actual authentication.

    ### Why This Config?
    In development or testing environments, you might not have a fully configured
    authentication system. `NoAuthConfig` allows you to proceed without authentication
    by supplying a fake user identity, ensuring your code can run and be tested even
    before the authentication integration is complete.
    """

    NAME: str = Field("Melanie Musterfrau", description="The user's displayed name.")
    EMAIL: str = Field("melanie.musterfrau@bbv.ch", description="The user's email (often used as a login or unique identifier).")
    OID: str = Field(
        ...,
        description="A unique OID (Object ID) for the user. Defaults to a UUID.",
        default_factory=lambda: str(uuid.uuid4()),
    )
    ROLES: List[str] = Field(["AllAgents"], description="A list of roles this user possesses.")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
