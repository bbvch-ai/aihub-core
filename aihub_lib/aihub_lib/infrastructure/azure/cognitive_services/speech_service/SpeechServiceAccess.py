from azure.cognitiveservices.speech import SpeechConfig

from aihub_lib.infrastructure.azure.cognitive_services.CognitiveServiceAccess import CognitiveServiceAccess
from aihub_lib.infrastructure.azure.cognitive_services.speech_service.SpeechServiceConfig import SpeechServiceConfig


class SpeechServiceAccess(CognitiveServiceAccess):
    _primary_admin_key = None
    _resource_group_name = None
    _search_service_name = None
    _service_endpoint = None
    _region = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SpeechServiceAccess, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # If the key and region are provided in the config, use them
        if SpeechServiceConfig().SPEECH_SERVICE_KEY and SpeechServiceConfig().SPEECH_SERVICE_REGION:
            self._region = SpeechServiceConfig().SPEECH_SERVICE_REGION
            self.speech_config = SpeechConfig(
                subscription=SpeechServiceConfig().SPEECH_SERVICE_KEY,
                region=self._region,
            )
            return

        super()._initialize()

        self._resource_group_name = (
            SpeechServiceConfig().SPEECH_SERVICE_RESOURCE_GROUP_NAME or f"{self._app}-{self._env}-rg-{self._region}"
        )
        self._speech_service_account_name = (
            SpeechServiceConfig().SPEECH_SERVICE_NAME or f"{self._app}-{self._env}-srch-{self._region}"
        )

        account = self._client.accounts.get(self._resource_group_name, self._speech_service_account_name)
        self._region = account.location

        keys = self._client.accounts.list_keys(self._resource_group_name, self._speech_service_account_name)
        self._primary_admin_key = keys.primary_key

        self.speech_config = SpeechConfig(subscription=self._primary_admin_key, region=self._region)

    def get_config(self):
        return self.speech_config

    def get_region(self):
        return self._region
