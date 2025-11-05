import logging

from adlfs import AzureBlobFileSystem
from azure.storage.filedatalake import DataLakeServiceClient

from aihub_lib.infrastructure.azure.AzureSettings import AzureSettings
from aihub_lib.infrastructure.azure.data_lake.AzureDataLakeSettings import AzureDataLakeSettings

logger = logging.getLogger(__name__)


class DataLakeAccess:
    """
    A singleton class to provide centralized access to Azure Data Lake Storage.

    Authentication:
    - Prefers CONNECTION_STRING for explicit token-based authentication
    - Falls back to ENDPOINT-based authentication (requires azure-identity package)
    """

    _instance = None
    _app = None
    _region = None
    _storage_service_name = None
    _service_endpoint = None
    _credential = None
    _cached_fs_client: AzureBlobFileSystem | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataLakeAccess, cls).__new__(cls)  # noqa: UP008
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        settings = AzureDataLakeSettings()
        self._app = AzureSettings().APP_NAME
        self._region = AzureSettings().REGION_SHORT
        self._storage_service_name = settings.NAME or f"{self._app}st{self._region}datalake"
        self._service_endpoint = settings.ENDPOINT or f"https://{self._storage_service_name}.dfs.core.windows.net"

        # Prefer explicit connection string authentication
        if settings.CONNECTION_STRING:
            logger.info("Using explicit connection string authentication for Azure Data Lake")
            self.datalake_client = DataLakeServiceClient.from_connection_string(
                settings.CONNECTION_STRING.get_secret_value()
            )
            # For adlfs, we'll need to extract the connection string components
            # Connection strings typically include account_name and account_key
            conn_str = settings.CONNECTION_STRING.get_secret_value()
            self._credential = conn_str  # Store for later use with adlfs
        else:
            # Fallback to credential-based authentication (DEPRECATED)
            logger.warning(
                "Using implicit DefaultAzureCredential for Azure Data Lake authentication. "
                "This is deprecated and will be removed in a future version. "
                "Please set AZURE_DATA_LAKE_CONNECTION_STRING instead."
            )
            try:
                from azure.identity import DefaultAzureCredential

                self._credential = DefaultAzureCredential()
                self.datalake_client = DataLakeServiceClient(
                    account_url=self._service_endpoint,
                    credential=self._credential,
                )
            except ImportError as e:
                raise ImportError(
                    "azure-identity package is required for implicit authentication. "
                    "Please install it or use CONNECTION_STRING authentication instead."
                ) from e
        self._cached_fs_client = None

    def get_client(self) -> DataLakeServiceClient:
        return self.datalake_client

    def get_fs_client(self) -> AzureBlobFileSystem:
        if self._cached_fs_client is None:
            self._cached_fs_client = AzureBlobFileSystem(
                account_name=self._storage_service_name, credential=self._credential
            )
        return self._cached_fs_client

    def get_storage_account_name(self) -> str:
        return self._storage_service_name
