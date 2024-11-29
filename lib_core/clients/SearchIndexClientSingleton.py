from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.search import SearchManagementClient
from azure.search.documents.indexes import SearchIndexClient

from aihub.config.BaseConfig import BaseConfig
from aihub.config.CognitiveSearchConfig import CognitiveSearchConfig


class SearchIndexClientSingleton:
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
            cls._instance = super(SearchIndexClientSingleton, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        if CognitiveSearchConfig().COGNITIVE_SEARCH_ENDPOINT and CognitiveSearchConfig().COGNITIVE_SEARCH_API_KEY:
            self.index_client = SearchIndexClient(
                endpoint=CognitiveSearchConfig().COGNITIVE_SEARCH_ENDPOINT,
                credential=AzureKeyCredential(CognitiveSearchConfig().COGNITIVE_SEARCH_API_KEY),
            )
            return

        self._env = BaseConfig().ENVIRONMENT
        self._app = BaseConfig().APP_NAME
        self._region = BaseConfig().REGION_SHORT
        self._subscription_name = BaseConfig().AZURE_SUBSCRIPTION_NAME
        self._resource_group_name = (
            CognitiveSearchConfig().COGNITIVE_SEARCH_RESOURCE_GROUP_NAME or f"{self._app}-{self._env}-rg-{self._region}"
        )
        self._search_service_name = (
            CognitiveSearchConfig().COGNITIVE_SEARCH_NAME or f"{self._app}-{self._env}-srch-{self._region}"
        )
        self._service_endpoint = f"https://{self._search_service_name}.search.windows.net"

        credential = DefaultAzureCredential()
        subscription_client = SubscriptionClient(credential)
        subscriptions = subscription_client.subscriptions.list()
        subscription_id = None
        for subscription in subscriptions:
            if subscription.display_name == self._subscription_name:
                subscription_id = subscription.subscription_id
                break

        if subscription_id is None:
            raise ValueError(f"Subscription with name '{self._subscription_name}' not found.")

        search_client = SearchManagementClient(credential, subscription_id)

        keys = search_client.admin_keys.get(self._resource_group_name, self._search_service_name)
        self._primary_admin_key = keys.primary_key

        self.index_client = SearchIndexClient(
            endpoint=self._service_endpoint,
            credential=AzureKeyCredential(self._primary_admin_key),
        )

    def get_client(self):
        return self.index_client
