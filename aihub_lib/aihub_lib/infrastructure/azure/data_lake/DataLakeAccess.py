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

        # Try to use the storage account key if available, otherwise fall back to DefaultAzureCredential
        account_key = DataLakeConfig().DATA_LAKE_ACCOUNT_KEY
        if account_key:
            self.datalake_client = DataLakeServiceClient(
                account_url=self._service_endpoint,
                credential=account_key,
            )
            self.file_system = AzureBlobFileSystem(account_name=self._storage_service_name, account_key=account_key)
        else:
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
