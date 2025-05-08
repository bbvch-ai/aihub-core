from typing import ClassVar, Optional

from pydantic import Field
from aihub_iac.azure.modules.nats.NatsConfig import NatsConfig
from aihub_iac.azure.resources.BaseConfig import BaseConfig

from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class AgentConfig(BaseConfig):

    _registry_settings: ClassVar[RegistrySettings] = RegistrySettings()

    # Docker Image settings
    repo_image_url: str = Field(description="URL of the Docker repository")
    docker_image_tag: str = Field(description="Tag of the Docker image")

    # Registry settings
    registry_user: str = Field(
        default_factory=lambda: AgentConfig._registry_settings.REGISTRY_USER,
        description="Registry username for authentication",
    )
    registry_pat: str = Field(
        default_factory=lambda: AgentConfig._registry_settings.REGISTRY_PAT,
        description="Registry personal access token for authentication",
    )

    # Service endpoints
    phoenix_auth_token: str = Field(description="Authentication token for Phoenix service")

    # resources
    cpu: float = Field(default=0.5, description="CPU allocation in cores")
    memory_in_gb: float = Field(default=0.5, description="Memory allocation in GB")

    # AI resources
    ai_search_name: Optional[str] = Field(default=None, description="Name of the AI search service")
    ai_search_resource_group: Optional[str] = Field(default=None, description="Resource group for AI search")
    doc_store_name: Optional[str] = Field(default=None, description="Name of the document store")
    doc_store_resource_group: Optional[str] = Field(default=None, description="Resource group for document store")

    doc_store_cosmos_account_name: Optional[str] = Field(
        default=None, description="Name of the Cosmos DB account for document storage"
    )
    doc_store_cosmos_resource_group: Optional[str] = Field(
        default=None, description="Resource group for Cosmos DB document storage"
    )

    # Other settings
    log_level: str = Field(default="WARNING", description="Logging level for the application")

    @property
    def phoenix_service_name(self) -> str:
        """Generate the phoenix service name"""
        return self.resource_namer.app_service_name("phoenix")

    @property
    def effective_docker_image(self) -> str:
        """Generate the full docker image string"""
        return f"{self.repo_image_url}:{self.docker_image_tag}"

    @property
    def effective_doc_store_cosmos_account_name(self) -> str:
        """Generate the cosmos name"""
        return self.doc_store_cosmos_account_name or self.resource_namer.cosmos_name("docstore")

    @property
    def effective_doc_store_cosmos_resource_group(self) -> str:
        """Get the effective cosmos resource group, using the configured value or the default"""
        return self.doc_store_cosmos_resource_group or self.resource_group

    @property
    def effective_ai_search_name(self) -> str:
        """Generate the AI search name, using the configured value or a default based on the project name, AI search service, and location"""
        return self.ai_search_name or f"{self.resource_namer.ai_search_name}"

    @property
    def effective_ai_search_resource_group(self) -> str:
        """Get the effective cosmos resource group, using the configured value or the default"""
        return self.ai_search_resource_group or self.resource_group

    @property
    def nats_container_group_name(self) -> str:
        return self.resource_namer.container_instance_name(NatsConfig.DEFAULT_NATS_SUFFIX)

    def container_group_name(self, name: str) -> str:
        return self.resource_namer.container_group_name(name)

    def container_instance_name(self, name: str) -> str:
        return self.resource_namer.container_instance_name(name)
