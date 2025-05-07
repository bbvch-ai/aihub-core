from pydantic import BaseModel, Field

from aihub_iac.azure.constants.resources import STORAGE_ACCOUNT
from aihub_iac.azure.resources.BaseConfig import BaseConfig


class StorageConfig(BaseConfig):

    def get_storage_account_name(self, service_name: str) -> str:
        return self.resource_namer.storage_account_name(service_name)
