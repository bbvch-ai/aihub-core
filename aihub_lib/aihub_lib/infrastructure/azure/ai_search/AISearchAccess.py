from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.mgmt.search import SearchManagementClient
from azure.search.documents.indexes import SearchIndexClient

from aihub_lib.infrastructure.azure.AzureBaseConfig import AzureBaseConfig
from aihub_lib.infrastructure.azure.ai_search.AISearchConfig import AISearchConfig


class AISearchAccess:
    _instance = None
    _primary_admin_key = None
    _env = None
    _app = None
    _subscription_name = None
    _resource_group_name = None
    _search_service_name = None
    _service_endpoint = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AISearchAccess, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        if AISearchConfig().COGNITIVE_SEARCH_ENDPOINT and AISearchConfig().COGNITIVE_SEARCH_API_KEY:
            self.index_client = SearchIndexClient(
                endpoint=AISearchConfig().COGNITIVE_SEARCH_ENDPOINT,
                credential=AzureKeyCredential(AISearchConfig().COGNITIVE_SEARCH_API_KEY),
            )
            return

        self._app = AzureBaseConfig().APP_NAME
        self._region = AzureBaseConfig().REGION_SHORT
        self._subscription_id = AzureBaseConfig().AZURE_SUBSCRIPTION_ID
        self._resource_group_name = (
            AISearchConfig().COGNITIVE_SEARCH_RESOURCE_GROUP_NAME or f"{self._app}-rg-{self._region}"
        )
        self._search_service_name = AISearchConfig().COGNITIVE_SEARCH_NAME or f"{self._app}-srch-{self._region}"
        self._service_endpoint = f"https://{self._search_service_name}.search.windows.net"

        credential = DefaultAzureCredential()

        search_client = SearchManagementClient(credential, self._subscription_id)

        keys = search_client.admin_keys.get(self._resource_group_name, self._search_service_name)
        self._primary_admin_key = keys.primary_key

        self.index_client = SearchIndexClient(
            endpoint=self._service_endpoint,
            credential=AzureKeyCredential(self._primary_admin_key),
        )

    def get_client(self):
        return self.index_client
