from pydantic import BaseModel, Field, computed_field
from aihub_iac.azure.constants.resources import COSMOS, AI_SEARCH_SERVICE, APP_SERVICE
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class AgentConfig(BaseModel):

    # Project and environment settings
    project_name: str
    location: str
    location_short: str
    resource_group: str
    subscription_id: str

    # Docker Image settings
    repo_image_url: str
    image_tag: str

    # Registry settings
    registry_user: str
    registry_pat: str

    # Service endpoints
    phoenix_service_name: str
    phoenix_auth_token: str

    # resources
    cpu: float = 0.5
    memory_in_gb: float = 0.5

    # AI resources
    ai_search_name: str | None = None
    ai_search_resource_group: str | None = None
    doc_store_name: str | None = None
    doc_store_resource_group: str | None = None

    doc_store_cosmos_account_name: str | None
    doc_store_cosmos_resource_group: str | None

    # Other settings
    log_level: str = Field(default="WARNING")

    @classmethod
    def from_env(
        cls,
        repo_image_url: str,
        docker_image_tag: str,
        phoenix_auth_token: str,
        doc_store_cosmos_account_name: str | None = None,
        doc_store_cosmos_resource_group: str | None = None,
        ai_search_name: str | None = None,
        ai_search_resource_group: str | None = None,
    ):

        project_settings = ProjectSettings()
        registry_settings = RegistrySettings()

        return cls(
            project_name=project_settings.APP_NAME,
            location=project_settings.LOCATION,
            location_short=project_settings.LOCATION_SHORT,
            resource_group=project_settings.RESOURCE_GROUP,
            subscription_id=project_settings.ARM_SUBSCRIPTION_ID,
            repo_image_url=repo_image_url,
            image_tag=docker_image_tag,
            registry_user=registry_settings.REGISTRY_USER,
            registry_pat=registry_settings.REGISTRY_PAT,
            phoenix_service_name=f"{project_settings.APP_NAME}-{APP_SERVICE}-{project_settings.LOCATION_SHORT}-phoenix",
            phoenix_auth_token=phoenix_auth_token,
            ai_search_name=ai_search_name,
            ai_search_resource_group=ai_search_resource_group,
            doc_store_cosmos_account_name=doc_store_cosmos_account_name,
            doc_store_cosmos_resource_group=doc_store_cosmos_resource_group,
        )

    @property
    def effective_docker_image(self) -> str:
        """Generate the full docker image string"""
        return f"{self.repo_image_url}:{self.image_tag}"

    @property
    def effective_doc_store_cosmos_account_name(self) -> str:
        """Generate the cosmos name"""
        return self.doc_store_cosmos_account_name or f"{self.project_name}-{COSMOS}-{self.location_short}-docstore"

    @property
    def effective_doc_store_cosmos_resource_group(self) -> str:
        """Get the effective cosmos resource group, using the configured value or the default"""
        return self.doc_store_cosmos_resource_group or self.resource_group

    @property
    def effective_ai_search_name(self) -> str:
        """Generate the cosmos name"""
        return self.ai_search_name or f"{self.project_name}-{AI_SEARCH_SERVICE}-{self.location_short}"

    @property
    def effective_ai_search_resource_group(self) -> str:
        """Get the effective cosmos resource group, using the configured value or the default"""
        return self.ai_search_resource_group or self.resource_group
