import logging

from azure.storage.blob import BlobServiceClient

from aihub_lib.infrastructure.azure.AzureSettings import AzureSettings
from aihub_lib.infrastructure.azure.blob_storage.AzureBlobStorageSettings import AzureBlobStorageSettings

logger = logging.getLogger(__name__)


class BlobStorageAccess:
    """
    A singleton class to provide centralized access to Azure Blob Storage.

    Authentication:
    - Prefers CONNECTION_STRING for explicit token-based authentication
    - Falls back to ENDPOINT-based authentication (requires azure-identity package)
    """

    _instance = None
    _app = None
    _region = None
    _storage_service_name = None
    _service_endpoint = None
    _blob_service_client: BlobServiceClient

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BlobStorageAccess, cls).__new__(cls)  # noqa: UP008
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._blob_service_client = BlobServiceClient.from_connection_string(
            AzureBlobStorageSettings().CONNECTION_STRING.get_secret_value()
        )

    def get_account_name(self) -> str:
        return self._storage_service_name

    def get_service_endpoint(self):
        return self._service_endpoint

    def get_blob_service_client(self) -> BlobServiceClient:
        return self._blob_service_client

    def get_url_signing_secret(self) -> str:
        return AzureBlobStorageSettings().URL_SIGNING_SECRET
