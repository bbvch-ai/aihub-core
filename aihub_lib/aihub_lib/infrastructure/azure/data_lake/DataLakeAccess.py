from typing import Optional

from adlfs import AzureBlobFileSystem
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient

from aihub_lib.infrastructure.azure.AzureBaseConfig import AzureBaseConfig
from aihub_lib.infrastructure.azure.data_lake.DataLakeConfig import DataLakeConfig


class DataLakeAccess:
    _instance = None
    _env = None
    _app = None
    _storage_service_name = None
    _service_endpoint = None
    _credential = None
    _cached_fs_client: Optional[AzureBlobFileSystem] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataLakeAccess, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._app = AzureBaseConfig().APP_NAME
        self._region = AzureBaseConfig().REGION_SHORT
        self._storage_service_name = DataLakeConfig().DATA_LAKE_NAME or f"{self._app}st{self._region}datalake"
        self._service_endpoint = (
            DataLakeConfig().DATA_LAKE_ENDPOINT or f"https://{self._storage_service_name}.dfs.core.windows.net"
        )

        self._credential = DefaultAzureCredential()
        self.datalake_client = DataLakeServiceClient(
            account_url=self._service_endpoint,
            credential=self._credential,
        )
        self._cached_fs_client = None

    def get_client(self) -> DataLakeServiceClient:
        return self.datalake_client

    def get_fs_client(self) -> AzureBlobFileSystem:
        if self._cached_fs_client is None:
            self._cached_fs_client = AzureBlobFileSystem(account_name=self._storage_service_name)
        return self._cached_fs_client

    def get_storage_account_name(self) -> str:
        return self._storage_service_name
