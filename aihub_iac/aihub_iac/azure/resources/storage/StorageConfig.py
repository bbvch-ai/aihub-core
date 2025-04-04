from pydantic import BaseModel, Field

from aihub_iac.azure.constants.resources import STORAGE_ACCOUNT


class StorageConfig(BaseModel):
    """Base configuration for storage resources"""

    resource_group: str
    location: str
    project_name: str
    location_short: str

    def get_storage_account_name(self, service_name: str) -> str:
        """Generate a storage account name"""
        return f"{self.project_name}{STORAGE_ACCOUNT}{self.location_short}{service_name}"
