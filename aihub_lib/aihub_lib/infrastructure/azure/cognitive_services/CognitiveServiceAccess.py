from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

from aihub_lib.infrastructure.azure.AzureSettings import AzureSettings


class CognitiveServiceAccess:
    _instance = None
    _env = None
    _app = None
    _subscription_name = None
    _azure_credential = None
    _client = None

    def _initialize(self):
        self._app = AzureSettings().APP_NAME
        self._region = AzureSettings().REGION_SHORT
        self._subscription_id = AzureSettings().SUBSCRIPTION_ID
        self._azure_credential = DefaultAzureCredential()

        self._client = CognitiveServicesManagementClient(self._azure_credential, self._subscription_id)
