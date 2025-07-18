from typing import Annotated, ClassVar

from pydantic import Field

from aihub_iac.azure.constants.suffix import DEFAULT_DOCSTORE_SUFFIX
from aihub_iac.azure.resources.BaseConfig import BaseConfig
from aihub_iac.azure.settings.PostgresAuthSettings import PostgresAuthSettings


class StoresConfig(BaseConfig):
    """Configuration class for Nats infrastructure"""

    _postgres_settings: ClassVar[PostgresAuthSettings] = PostgresAuthSettings()

    API_COSMOS_SUBNET_CIDR: ClassVar[str] = "10.0.37.0/24"
    SEARCH_SUBNET_CIDR: ClassVar[str] = "10.0.34.0/24"
    PG_SUBNET_CIDR: ClassVar[str] = "10.0.4.0/24"
    COSMOS_SUBNET_CIDR: ClassVar[str] = "10.0.33.0/24"

    postgres_username: Annotated[
        str,
        Field(
            default_factory=lambda: StoresConfig._postgres_settings.POSTGRES_USERNAME,
            description="Username for the PostgreSQL database",
        ),
    ]
    postgres_password: Annotated[
        str,
        Field(
            default_factory=lambda: StoresConfig._postgres_settings.POSTGRES_PASSWORD,
            description="Password for the PostgreSQL database",
        ),
    ]

    @property
    def ai_search_service_name(self) -> str:
        return self.resource_namer.ai_search_name()

    @property
    def doc_store_name(self) -> str:
        return self.resource_namer.cosmos_name(DEFAULT_DOCSTORE_SUFFIX)

    @property
    def store_name(self) -> str:
        return self.resource_namer.cosmos_name()

    @property
    def postgres_name(self) -> str:
        return self.resource_namer.postgres_name()
