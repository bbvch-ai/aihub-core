from typing import Annotated, ClassVar

from pydantic import Field

from aihub_iac.azure.constants.suffix import DEFAULT_NATS_SUFFIX
from aihub_iac.azure.resources.BaseConfig import BaseConfig
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class AgentConfig(BaseConfig):
    _registry_settings: ClassVar[RegistrySettings] = RegistrySettings()

    # Docker Image settings
    repo_image_url: Annotated[str, Field(description="URL of the Docker repository")]
    docker_image_tag: Annotated[str, Field(description="Tag of the Docker image")]

    # Registry settings
    registry_user: Annotated[
        str,
        Field(
            default_factory=lambda: AgentConfig._registry_settings.REGISTRY_USER,
            description="Registry username for authentication",
        ),
    ]
    registry_pat: Annotated[
        str,
        Field(
            default_factory=lambda: AgentConfig._registry_settings.REGISTRY_PAT,
            description="Registry personal access token for authentication",
        ),
    ]

    # Service endpoints
    phoenix_auth_token: Annotated[str, Field(description="Authentication token for Phoenix service")]

    # resources
    cpu: Annotated[float, Field(description="CPU allocation in cores")] = 0.5
    memory_in_gb: Annotated[float, Field(description="Memory allocation in GB")] = 0.5

    # AI resources
    ai_search_name: Annotated[str | None, Field(description="Name of the AI search service")] = None
    ai_search_resource_group: Annotated[str | None, Field(description="Resource group for AI search")] = None
    doc_store_name: Annotated[str | None, Field(description="Name of the document store")] = None
    doc_store_resource_group: Annotated[str | None, Field(description="Resource group for document store")] = None

    doc_store_cosmos_account_name: Annotated[
        str | None, Field(description="Name of the Cosmos DB account for document storage")
    ] = None
    doc_store_cosmos_resource_group: Annotated[
        str | None, Field(description="Resource group for Cosmos DB document storage")
    ] = None

    # Other settings
    log_level: Annotated[str, Field(description="Logging level for the application")] = "WARNING"

    additional_env_vars: Annotated[
        dict[str, str | dict[str, str]],
        Field(
            description="Additional environment variables to pass to the agent "
            "container, can be plain values or secret references",
        ),
    ] = {}

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
        """
        Generate the AI search name, using the configured value or a default
        based on the project name, AI search service, and location
        """
        return self.ai_search_name or self.resource_namer.ai_search_name()

    @property
    def effective_ai_search_resource_group(self) -> str:
        """Get the effective cosmos resource group, using the configured value or the default"""
        return self.ai_search_resource_group or self.resource_group

    @property
    def nats_container_group_name(self) -> str:
        return self.resource_namer.container_instance_name(DEFAULT_NATS_SUFFIX)

    def container_group_name(self, name: str) -> str:
        return self.resource_namer.container_group_name(name)

    def container_instance_name(self, name: str) -> str:
        return self.resource_namer.container_instance_name(name)
