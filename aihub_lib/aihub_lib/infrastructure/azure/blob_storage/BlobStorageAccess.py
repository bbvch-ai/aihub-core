from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from aihub_lib.infrastructure.azure.AzureSettings import AzureSettings
from aihub_lib.infrastructure.azure.blob_storage.AzureBlobStorageSettings import AzureBlobStorageSettings


class BlobStorageAccess:
    """
    A singleton class to provide centralized access to Azure Blob Storage
    using DefaultAzureCredential for authentication.
    """

    _instance = None
    _app = None
    _region = None
    _storage_service_name = None
    _service_endpoint = None
    _credential: DefaultAzureCredential
    _blob_service_client: BlobServiceClient

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BlobStorageAccess, cls).__new__(cls)  # noqa: UP008
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._app = AzureSettings().APP_NAME
        self._region = AzureSettings().REGION_SHORT
        self._storage_service_name = AzureBlobStorageSettings().NAME or f"{self._app}st{self._region}datalake"
        self._service_endpoint = (
            AzureBlobStorageSettings().ENDPOINT or f"https://{self._storage_service_name}.blob.core.windows.net"
        )

        self._credential = DefaultAzureCredential()
        self._blob_service_client = BlobServiceClient(account_url=self._service_endpoint, credential=self._credential)

    def get_account_name(self) -> str:
        return self._storage_service_name

    def get_service_endpoint(self):
        return self._service_endpoint

    def get_blob_service_client(self) -> BlobServiceClient:
        return self._blob_service_client

    def get_url_signing_secret(self) -> str:
        return AzureBlobStorageSettings().URL_SIGNING_SECRET
