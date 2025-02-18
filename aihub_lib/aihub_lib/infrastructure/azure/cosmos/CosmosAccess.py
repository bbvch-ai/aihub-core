from azure.identity import DefaultAzureCredential
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.resource import SubscriptionClient

from aihub_lib.infrastructure.azure.BaseConfig import BaseConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosConfig import CosmosConfig


class CosmosAccess:
    _instance = None
    _connection_string = None
    _env = None
    _app = None
    _subscription_name = None
    _resource_group_name = None
    _cosmos_account_name = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CosmosAccess, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        if CosmosConfig().COSMOS_CONNECTION_STRING:
            self._connection_string = CosmosConfig().COSMOS_CONNECTION_STRING
            return
        self._app = BaseConfig().APP_NAME
        self._region = BaseConfig().REGION_SHORT
        self._subscription_id = BaseConfig().AZURE_SUBSCRIPTION_ID
        self._resource_group_name = CosmosConfig().COSMOS_RESOURCE_GROUP_NAME or f"{self._app}-rg-{self._region}"
        self._cosmos_account_name = CosmosConfig().COSMOS_ACCOUNT_NAME or f"{self._app}-cos-{self._region}"

        self._connection_string = self._fetch_connection_string()

    def _fetch_connection_string(self):
        if CosmosConfig().COSMOS_CONNECTION_STRING:
            return CosmosConfig().COSMOS_CONNECTION_STRING
        credential = DefaultAzureCredential()
        cosmos_client = CosmosDBManagementClient(credential, self._subscription_id)

        # Retrieve the connection string
        database_accounts = cosmos_client.database_accounts
        keys = database_accounts.list_connection_strings(self._resource_group_name, self._cosmos_account_name)
        return keys.connection_strings[0].connection_string

    def get_connection_string(self):
        return self._connection_string
