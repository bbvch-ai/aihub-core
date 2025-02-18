from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

from aihub_lib.infrastructure.azure.BaseConfig import BaseConfig


class CognitiveServiceAccess:
    _instance = None
    _env = None
    _app = None
    _subscription_name = None
    _azure_credential = None
    _client = None

    def _initialize(self):
        self._app = BaseConfig().APP_NAME
        self._region = BaseConfig().REGION_SHORT
        self._subscription_id = BaseConfig().AZURE_SUBSCRIPTION_ID
        self._azure_credential = DefaultAzureCredential()

        self._client = CognitiveServicesManagementClient(self._azure_credential, self._subscription_id)
