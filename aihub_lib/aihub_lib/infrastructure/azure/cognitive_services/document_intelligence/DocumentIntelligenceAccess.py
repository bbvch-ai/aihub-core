from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from aihub_lib.infrastructure.azure.cognitive_services.document_intelligence.AzureDocumentIntelligenceSettings import (
    AzureDocumentIntelligenceSettings,
)


class DocumentIntelligenceAccess:
    """
    A singleton class to provide centralized access to Azure Document Intelligence.

    Authentication uses explicit API key (token-based authentication).
    """

    _instance = None
    di_client: DocumentIntelligenceClient

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DocumentIntelligenceAccess, cls).__new__(cls)  # noqa: UP008
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        settings = AzureDocumentIntelligenceSettings()

        self.di_client = DocumentIntelligenceClient(
            endpoint=settings.ENDPOINT,
            credential=AzureKeyCredential(settings.API_KEY.get_secret_value()),
            api_version=settings.API_VERSION,
        )

    def get_client(self):
        return self.di_client
