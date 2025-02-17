from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.resource import SubscriptionClient

from aihub_lib.infrastructure.azure.AzureBaseConfig import AzureBaseConfig


class CognitiveServiceAccess:
    _instance = None
    _env = None
    _app = None
    _subscription_name = None
    _azure_credential = None
    _client = None

    def _initialize(self):
        self._env = AzureBaseConfig().ENVIRONMENT
        self._app = AzureBaseConfig().APP_NAME
        self._region = AzureBaseConfig().REGION_SHORT
        self._subscription_name = AzureBaseConfig().AZURE_SUBSCRIPTION_NAME
        self._azure_credential = DefaultAzureCredential()

        # Otherwise, get the key and region from the Azure Cognitive Services account
        subscription_client = SubscriptionClient(self._azure_credential)
        subscriptions = subscription_client.subscriptions.list()
        subscription_id = None
        for subscription in subscriptions:
            if subscription.display_name == self._subscription_name:
                subscription_id = subscription.subscription_id
                break

        if subscription_id is None:
            raise ValueError(f"Subscription with name '{self._subscription_name}' not found.")

        self._client = CognitiveServicesManagementClient(self._azure_credential, subscription_id)
