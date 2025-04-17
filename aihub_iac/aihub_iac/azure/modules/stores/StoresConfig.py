from pydantic import BaseModel, computed_field

from aihub_iac.azure.constants.resources import AI_SEARCH_SERVICE, COSMOS, POSTGRES
from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig
from aihub_iac.azure.settings.PostgresAuthSettings import PostgresAuthSettings
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings


class StoresConfig(BaseModel):
    """Configuration class for Nats infrastructure"""

    # Required fields
    project_name: str
    location: str
    location_short: str
    resource_group: str
    subscription_id: str

    postgres_username: str
    postgres_password: str

    @classmethod
    def from_env(cls) -> "StoresConfig":
        """Create a configuration from environment variables"""
        project_settings = ProjectSettings()
        postgres_auth_settings = PostgresAuthSettings()

        return cls(
            project_name=project_settings.APP_NAME,
            location=project_settings.LOCATION,
            location_short=project_settings.LOCATION_SHORT,
            resource_group=project_settings.RESOURCE_GROUP,
            subscription_id=project_settings.ARM_SUBSCRIPTION_ID,
            postgres_username=postgres_auth_settings.POSTGRES_USERNAME,
            postgres_password=postgres_auth_settings.POSTGRES_PASSWORD,
        )

    @property
    def ai_search_service_name(self) -> str:
        return f"{self.project_name}-{AI_SEARCH_SERVICE}-{self.location_short}"

    @property
    def doc_store_name(self) -> str:
        return f"{self.project_name}-{COSMOS}-{self.location_short}-docstore"

    @property
    def store_name(self) -> str:
        return f"{self.project_name}-{COSMOS}-{self.location_short}"

    @property
    def postgres_name(self) -> str:
        return f"{self.project_name}-{POSTGRES}-{self.location_short}"
