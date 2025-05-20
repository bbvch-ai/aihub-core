from typing import Optional

from pydantic import BaseModel

from aihub_iac.azure.constants.resources import (
    AI_SEARCH_SERVICE,
    APP_SERVICE,
    CONTAINER_APP,
    CONTAINER_APP_ENVIRONMENT,
    CONTAINER_GROUP,
    CONTAINER_INSTANCE,
    COSMOS,
    LOG_WORKSPACE,
    POSTGRES,
    V_NET,
)


class ResourceNamer(BaseModel):
    """
    Class responsible for creating standardized Azure resource names
    based on project name and location.
    """

    project_name: str
    location_short: str

    def generate_name(self, resource_type: str, suffix: Optional[str] = None) -> str:
        """
        Generate a standardized resource name following the pattern:
        {project_name}-{resource_type}-{location_short}[-{suffix}]

        Args:
            resource_type: The type of resource (e.g., 'cosmos', 'app-service')
            suffix: Optional suffix to append to the name

        Returns:
            Formatted resource name
        """
        name_parts = [self.project_name, resource_type, self.location_short]
        if suffix:
            name_parts.append(suffix)

        return "-".join(name_parts)

    def cosmos_name(self, suffix: Optional[str] = None) -> str:
        """Generate a cosmos DB account name"""
        return self.generate_name(COSMOS, suffix)

    def app_service_name(self, suffix: Optional[str] = None) -> str:
        """Generate an app service name"""
        return self.generate_name(APP_SERVICE, suffix)

    def postgres_name(self, suffix: Optional[str] = None) -> str:
        """Generate an app service name"""
        return self.generate_name(POSTGRES, suffix)

    def ai_search_name(self, suffix: Optional[str] = None) -> str:
        """Generate an AI search service name"""
        return self.generate_name(AI_SEARCH_SERVICE, suffix)

    def container_app_name(self, suffix: Optional[str] = None) -> str:
        """Generate an AI search service name"""
        return self.generate_name(CONTAINER_APP, suffix)

    def container_app_environment_name(self, suffix: Optional[str] = None) -> str:
        return self.generate_name(CONTAINER_APP_ENVIRONMENT, suffix)

    def container_instance_name(self, suffix: Optional[str] = None) -> str:
        return self.generate_name(CONTAINER_INSTANCE, suffix)

    def container_group_name(self, suffix: Optional[str] = None) -> str:
        return self.generate_name(CONTAINER_GROUP, suffix)

    def log_workspace(self, suffix: Optional[str] = None) -> str:
        return self.generate_name(LOG_WORKSPACE, suffix)

    def v_net_name(self, suffix: Optional[str] = None) -> str:
        return self.generate_name(V_NET, suffix)

    def storage_account_name(self, suffix: Optional[str] = None) -> str:
        """
        Generate a storage account name.
        Note: Storage accounts have specific naming restrictions:
        - Only lowercase letters and numbers
        - 3-24 characters
        - No hyphens
        """
        base_name = self.generate_name("st", suffix).replace("-", "").lower()
        # Ensure it's no longer than 24 characters
        return base_name[:24]

    def key_vault_name(self, suffix: Optional[str] = None) -> str:
        return self.generate_name("kv", suffix)
