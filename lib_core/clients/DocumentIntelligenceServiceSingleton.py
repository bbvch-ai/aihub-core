from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from aihub.app.clients.CognitiveServiceSingleton import CognitiveServiceSingleton
from aihub.config.DocumentIntelligenceConfig import DocumentIntelligenceConfig


class DocumentIntelligenceServiceSingleton(CognitiveServiceSingleton):
    _primary_admin_key = None
    _resource_group_name = None
    _di_service_name = None
    _di_endpoint = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DocumentIntelligenceServiceSingleton, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # If the key and region are provided in the config, use them
        if (
            DocumentIntelligenceConfig().DOCUMENTINTELLIGENCE_ENDPOINT
            and DocumentIntelligenceConfig().DOCUMENTINTELLIGENCE_API_KEY
            and DocumentIntelligenceConfig().DOCUMENTINTELLIGENCE_API_VERSION
        ):
            self.di_client = DocumentIntelligenceClient(
                endpoint=DocumentIntelligenceConfig().DOCUMENTINTELLIGENCE_ENDPOINT,
                credential=AzureKeyCredential(DocumentIntelligenceConfig().DOCUMENTINTELLIGENCE_API_KEY),
                api_version=DocumentIntelligenceConfig().DOCUMENTINTELLIGENCE_API_VERSION,
            )
            return

        super()._initialize()

        self._resource_group_name = (
            DocumentIntelligenceConfig().DOCUMENTINTELLIGENCE_RESOURCE_GROUP_NAME
            or f"{self._app}-{self._env}-rg-{self._region}"
        )
        self._di_service_name = (
            DocumentIntelligenceConfig().DOCUMENTINTELLIGENCE_NAME or f"{self._app}-{self._env}-di-{self._region}"
        )

        account = self._client.accounts.get(self._resource_group_name, self._di_service_name)
        self._location = account.location
        self._di_endpoint = account.properties.endpoint

        keys = self._client.accounts.list_keys(self._resource_group_name, self._di_service_name)
        self._primary_admin_key = keys.primary_key

        self.di_client = DocumentIntelligenceClient(
            endpoint=account.properties.endpoint,
            credential=AzureKeyCredential(self._primary_admin_key),
            api_version=DocumentIntelligenceConfig().DOCUMENTINTELLIGENCE_API_VERSION,
        )

    def get_client(self):
        return self.di_client
