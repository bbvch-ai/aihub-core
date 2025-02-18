from adlfs import AzureBlobFileSystem
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient

from aihub_lib.infrastructure.azure.BaseConfig import BaseConfig
from aihub_lib.infrastructure.azure.data_lake import DataLakeConfig


class DataLakeAccess:
    _instance = None
    _env = None
    _app = None
    _storage_service_name = None
    _service_endpoint = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataLakeAccess, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._app = BaseConfig().APP_NAME
        self._region = BaseConfig().REGION_SHORT
        self._storage_service_name = DataLakeConfig().DATA_LAKE_NAME or f"{self._app}st{self._region}datalake"
        self._service_endpoint = (
            DataLakeConfig().DATA_LAKE_ENDPOINT or f"https://{self._storage_service_name}.dfs.core.windows.net"
        )

        credential = DefaultAzureCredential()
        self.datalake_client = DataLakeServiceClient(
            account_url=self._service_endpoint,
            credential=credential,
        )
        self.file_system = AzureBlobFileSystem(account_name=self._storage_service_name, credential=credential)

    def get_client(self) -> DataLakeServiceClient:
        return self.datalake_client

    def get_fs_client(self) -> AzureBlobFileSystem:
        return self.file_system

    def get_storage_account_name(self) -> str:
        return self._storage_service_name
