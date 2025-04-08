from pydantic import BaseModel, computed_field

from aihub_iac.azure.constants.resources import (
    LOG_WORKSPACE,
    CONTAINER_APP_ENVIRONMENT,
    STORAGE_ACCOUNT,
    APP_SERVICE,
    CONTAINER_APP,
)
from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings


class OpenWebUIConfig(BaseModel):
    """Configuration class for Nats infrastructure"""

    webui_name: str
    admin_email: str
    default_locale: str

    openai_api_key: str
    rag_openai_api_key: str
    audio_stt_openai_api_key: str
    audio_tts_openai_api_key: str
    images_openai_api_key: str
    jina_api_key: str

    oidc_client_id: str
    oidc_client_secret: str
    oidc_provider_url: str
    oidc_provider_name: str
