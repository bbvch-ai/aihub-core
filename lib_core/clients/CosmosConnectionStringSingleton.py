from azure.identity import DefaultAzureCredential
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.resource import SubscriptionClient

from lib_core.config.BaseConfig import BaseConfig
from lib_core.config.CosmosConfig import CosmosConfig


class CosmosConnectionStringSingleton:
    _instance = None
    _connection_string = None
    _env = None
    _app = None
    _subscription_name = None
    _resource_group_name = None
    _cosmos_account_name = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CosmosConnectionStringSingleton, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        if CosmosConfig().COSMOS_CONNECTION_STRING:
            self._connection_string = CosmosConfig().COSMOS_CONNECTION_STRING
            return
        self._env = BaseConfig().ENVIRONMENT
        self._app = BaseConfig().APP_NAME
        self._region = BaseConfig().REGION_SHORT
        self._subscription_name = BaseConfig().AZURE_SUBSCRIPTION_NAME
        self._resource_group_name = (
            CosmosConfig().COSMOS_RESOURCE_GROUP_NAME or f"{self._app}-{self._env}-rg-{self._region}"
        )
        self._cosmos_account_name = CosmosConfig().COSMOS_ACCOUNT_NAME or f"{self._app}-{self._env}-cos-{self._region}"

        self._connection_string = self._fetch_connection_string()

    def _fetch_connection_string(self):
        if CosmosConfig().COSMOS_CONNECTION_STRING:
            return CosmosConfig().COSMOS_CONNECTION_STRING
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

        cosmos_client = CosmosDBManagementClient(credential, subscription_id)

        # Retrieve the connection string
        database_accounts = cosmos_client.database_accounts
        keys = database_accounts.list_connection_strings(self._resource_group_name, self._cosmos_account_name)
        return keys.connection_strings[0].connection_string

    def get_connection_string(self):
        return self._connection_string
