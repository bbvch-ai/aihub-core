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
        settings = AzureBlobStorageSettings()
        self._app = AzureSettings().APP_NAME
        self._region = AzureSettings().REGION_SHORT
        self._storage_service_name = settings.NAME or f"{self._app}st{self._region}datalake"
        self._service_endpoint = settings.ENDPOINT or f"https://{self._storage_service_name}.blob.core.windows.net"

        # Prefer explicit connection string authentication
        if settings.CONNECTION_STRING:
            logger.info("Using explicit connection string authentication for Azure Blob Storage")
            self._blob_service_client = BlobServiceClient.from_connection_string(
                settings.CONNECTION_STRING.get_secret_value()
            )
        else:
            # Fallback to credential-based authentication (DEPRECATED)
            logger.warning(
                "Using implicit DefaultAzureCredential for Azure Blob Storage authentication. "
                "This is deprecated and will be removed in a future version. "
                "Please set AZURE_BLOB_STORAGE_CONNECTION_STRING instead."
            )
            try:
                from azure.identity import DefaultAzureCredential

                credential = DefaultAzureCredential()
                self._blob_service_client = BlobServiceClient(account_url=self._service_endpoint, credential=credential)
            except ImportError as e:
                raise ImportError(
                    "azure-identity package is required for implicit authentication. "
                    "Please install it or use CONNECTION_STRING authentication instead."
                ) from e

    def get_account_name(self) -> str:
        return self._storage_service_name

    def get_service_endpoint(self):
        return self._service_endpoint

    def get_blob_service_client(self) -> BlobServiceClient:
        return self._blob_service_client

    def get_url_signing_secret(self) -> str:
        return AzureBlobStorageSettings().URL_SIGNING_SECRET
