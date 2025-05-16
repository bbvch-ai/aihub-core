from azure.identity import DefaultAzureCredential
from azure.mgmt.cosmosdb import CosmosDBManagementClient

from aihub_lib.infrastructure.azure.AzureBaseConfig import AzureBaseConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.infrastructure.azure.cosmos.docstore.CosmosDocstoreConfig import CosmosDocstoreConfig


class CosmosDocstoreAccess(CosmosAccess):

    def _initialize(self):
        if CosmosDocstoreConfig().COSMOS_DOCSTORE_CONNECTION_STRING:
            self._connection_string = CosmosDocstoreConfig().COSMOS_DOCSTORE_CONNECTION_STRING
            return
        self._app = AzureBaseConfig().APP_NAME
        self._region = AzureBaseConfig().REGION_SHORT
        self._subscription_id = AzureBaseConfig().AZURE_SUBSCRIPTION_ID
        self._resource_group_name = CosmosDocstoreConfig().COSMOS_DOCSTORE_RESOURCE_GROUP_NAME or f"{self._app}-rg-{self._region}"
        self._cosmos_account_name = CosmosDocstoreConfig().COSMOS_DOCSTORE_ACCOUNT_NAME or f"{self._app}-cos-{self._region}-docstore"

        self._connection_string = self._fetch_connection_string()

    def _fetch_connection_string(self):
        if CosmosDocstoreConfig().COSMOS_DOCSTORE_CONNECTION_STRING:
            return CosmosDocstoreConfig().COSMOS_DOCSTORE_CONNECTION_STRING
        credential = DefaultAzureCredential()
        cosmos_client = CosmosDBManagementClient(credential, self._subscription_id)

        # Retrieve the connection string
        database_accounts = cosmos_client.database_accounts
        keys = database_accounts.list_connection_strings(self._resource_group_name, self._cosmos_account_name)
        return keys.connection_strings[0].connection_string
