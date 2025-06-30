from typing import Annotated, Optional

from pydantic import BaseModel, Field


class OpenWebUIConfig(BaseModel):
    """Configuration class for Nats infrastructure"""

    webui_name: Annotated[str, Field(description="Name of web UI")]
    admin_email: Annotated[str, Field(description="Admin email for web UI")]
    default_locale: Annotated[str, Field(description="Default locale for web UI")]

    webui_secret_key: Annotated[str, Field(description="Secret key for web UI")]

    aihub_api_key: Annotated[Optional[str], Field(description="AIHub API key")] = None
    custom_openai_api_key: Annotated[Optional[str], Field(description="OpenAI API key")] = None
    custom_rag_openai_api_key: Annotated[Optional[str], Field(description="OpenAI API key for RAG")] = None
    custom_audio_stt_openai_api_key: Annotated[Optional[str], Field(description="OpenAI API key for audio STT")] = None
    custom_audio_tts_openai_api_key: Annotated[Optional[str], Field(description="OpenAI API key for audio TTS")] = None
    custom_images_openai_api_key: Annotated[Optional[str], Field(description="OpenAI API key for images")] = None
    jina_api_key: Annotated[str, Field(description="Jina API key")]

    oidc_client_id: Annotated[str, Field(description="OIDC client ID")]
    oidc_client_secret: Annotated[str, Field(description="OIDC client secret")]
    oidc_provider_url: Annotated[str, Field(description="OIDC provider URL")]
    oidc_provider_name: Annotated[str, Field(description="OIDC provider name")]

    additional_env_vars: Annotated[dict, Field(description="Additional environment variables")] = {}

    @property
    def rag_openai_api_key(self) -> str:
        return self.custom_rag_openai_api_key or self.aihub_api_key

    @property
    def openai_api_key(self) -> str:
        return self.custom_rag_openai_api_key or self.aihub_api_key

    @property
    def audio_stt_openai_api_key(self) -> str:
        return self.custom_audio_stt_openai_api_key or self.aihub_api_key

    @property
    def audio_tts_openai_api_key(self) -> str:
        return self.custom_audio_tts_openai_api_key or self.aihub_api_key

    @property
    def images_openai_api_key(self) -> str:
        return self.custom_images_openai_api_key or self.aihub_api_key
