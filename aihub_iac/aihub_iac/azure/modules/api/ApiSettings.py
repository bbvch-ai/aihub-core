from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    API_REPO_IMAGE_URL: Annotated[Optional[str], Field(description="URL where the image for the api is stored")] = None
    API_IMAGE_TAG: Annotated[Optional[str], Field(description="image tag for the api")] = None
    API_APP_SERVICE_PLAN_NAME: Annotated[
        Optional[str], Field(description="name of the app service plan to use for the api")
    ] = None
    API_COSMOS_ACCOUNT_NAME: Annotated[
        Optional[str], Field(description="name of the cosmos account if not default (<APP_NAME>-cos-<LOCATION>-api)")
    ] = None
    API_COSMOS_RESOURCE_GROUP_NAME: Annotated[
        Optional[str],
        Field(
            description="resource group name where the cosmos is located if not in the same resource group as the bot",
        ),
    ] = None
    API_ANONYM_NAME: Annotated[Optional[str], Field(description="-")] = None
    API_ANONYM_EMAIL: Annotated[Optional[str], Field(description="-")] = None
    API_ANONYM_ROLES: Annotated[Optional[str], Field(description="-")] = None
    API_ANONYM_OID: Annotated[Optional[str], Field(description="-")] = None
    API_VERSION: Annotated[Optional[str], Field(description="version")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
